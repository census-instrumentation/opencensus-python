# Copyright 2017, OpenCensus Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import inspect
import logging
import sys

import flask
from google.rpc import code_pb2

from opencensus.trace import attributes_helper
from opencensus.trace import execution_context
from opencensus.trace import stack_trace
from opencensus.trace import status
from opencensus.trace import tracer as tracer_module
from opencensus.trace.exporters import print_exporter
from opencensus.trace.exporters.transports import sync
from opencensus.trace.ext import utils
from opencensus.trace.propagation import google_cloud_format
from opencensus.trace.samplers import always_on, probability


_FLASK_TRACE_HEADER = 'X_CLOUD_TRACE_CONTEXT'

HTTP_METHOD = attributes_helper.COMMON_ATTRIBUTES['HTTP_METHOD']
HTTP_URL = attributes_helper.COMMON_ATTRIBUTES['HTTP_URL']
HTTP_STATUS_CODE = attributes_helper.COMMON_ATTRIBUTES['HTTP_STATUS_CODE']

BLACKLIST_PATHS = 'BLACKLIST_PATHS'
GCP_EXPORTER_PROJECT = 'GCP_EXPORTER_PROJECT'
SAMPLING_RATE = 'SAMPLING_RATE'
TRANSPORT = 'TRANSPORT'
ZIPKIN_EXPORTER_SERVICE_NAME = 'ZIPKIN_EXPORTER_SERVICE_NAME'
ZIPKIN_EXPORTER_HOST_NAME = 'ZIPKIN_EXPORTER_HOST_NAME'
ZIPKIN_EXPORTER_PORT = 'ZIPKIN_EXPORTER_PORT'

log = logging.getLogger(__name__)


class FlaskMiddleware(object):
    DEFAULT_SAMPLER = always_on.AlwaysOnSampler
    DEFAULT_EXPORTER = print_exporter.PrintExporter
    DEFAULT_PROPAGATOR = google_cloud_format.GoogleCloudFormatPropagator

    """Flask middleware to automatically trace requests.

    :type app: :class: `~flask.Flask`
    :param app: A flask application.

    :type blacklist_paths: list
    :param blacklist_paths: Paths that do not trace.

    :type sampler: :class: `type`
    :param sampler: Class for creating new Sampler objects. It should extend
                    from the base :class:`.Sampler` type and implement
                    :meth:`.Sampler.should_sample`. Defaults to
                    :class:`.AlwaysOnSampler`. The rest options are
                    :class:`.AlwaysOffSampler`, :class:`.FixedRateSampler`.

    :type exporter: :class: `type`
    :param exporter: Class for creating new exporter objects. Default to
                     :class:`.PrintExporter`. The rest option is
                     :class:`.FileExporter`.

    :type propagator: :class: 'type'
    :param propagator: Class for creating new propagator objects. Default to
                       :class:`.GoogleCloudFormatPropagator`. The rest option
                       are :class:`.BinaryFormatPropagator`,
                       :class:`.TextFormatPropagator` and
                       :class:`.TraceContextPropagator`.
    """
    def __init__(self, app=None, blacklist_paths=None, sampler=None,
                 exporter=None, propagator=None):
        self.app = app
        self.blacklist_paths = blacklist_paths
        self.sampler = sampler
        self.exporter = exporter
        self.propagator = propagator

        if self.app is not None:
            self.init_app(app)

    def init_app(self, app):
        self.app = app

        # get settings from app config
        settings = self.app.config.get('OPENCENSUS_TRACE', {})

        self.sampler = (self.sampler
                        or settings.get('SAMPLER',
                                        self.DEFAULT_SAMPLER))
        self.exporter = (self.exporter
                         or settings.get('EXPORTER',
                                         self.DEFAULT_EXPORTER))
        self.propagator = (self.propagator
                           or settings.get('PROPAGATOR',
                                           self.DEFAULT_PROPAGATOR))

        # get params from app config
        params = self.app.config.get('OPENCENSUS_TRACE_PARAMS', {})

        self.blacklist_paths = params.get(BLACKLIST_PATHS,
                                          self.blacklist_paths)

        # Initialize the sampler
        if not inspect.isclass(self.sampler):
            pass  # handling of instantiated sampler
        elif self.sampler.__name__ == 'ProbabilitySampler':
            _rate = params.get(SAMPLING_RATE,
                               probability.DEFAULT_SAMPLING_RATE)
            self.sampler = self.sampler(_rate)
        else:
            self.sampler = self.sampler()

        transport = params.get(TRANSPORT, sync.SyncTransport)

        # Initialize the exporter
        if not inspect.isclass(self.exporter):
            pass  # handling of instantiated exporter
        elif self.exporter.__name__ == 'StackdriverExporter':
            _project_id = params.get(GCP_EXPORTER_PROJECT, None)
            self.exporter = self.exporter(
                project_id=_project_id,
                transport=transport)
        elif self.exporter.__name__ == 'ZipkinExporter':
            _zipkin_service_name = params.get(
                ZIPKIN_EXPORTER_SERVICE_NAME, 'my_service')
            _zipkin_host_name = params.get(
                ZIPKIN_EXPORTER_HOST_NAME, 'localhost')
            _zipkin_port = params.get(
                ZIPKIN_EXPORTER_PORT, 9411)
            self.exporter = self.exporter(
                service_name=_zipkin_service_name,
                host_name=_zipkin_host_name,
                port=_zipkin_port,
                transport=transport)
        else:
            self.exporter = self.exporter(transport=transport)

        # Initialize the propagator
        if inspect.isclass(self.propagator):
            self.propagator = self.propagator()

        self.setup_trace()

    def setup_trace(self):
        self.app.before_request(self._before_request)
        self.app.after_request(self._after_request)
        self.app.teardown_request(self._teardown_request)

    def _before_request(self):
        """A function to be run before each request.

        See: http://flask.pocoo.org/docs/0.12/api/#flask.Flask.before_request
        """
        # Do not trace if the url is blacklisted
        if utils.disable_tracing_url(flask.request.url, self.blacklist_paths):
            return

        try:
            header = get_flask_header()
            span_context = self.propagator.from_header(header)

            tracer = tracer_module.Tracer(
                span_context=span_context,
                sampler=self.sampler,
                exporter=self.exporter,
                propagator=self.propagator)

            span = tracer.start_span()

            # Set the span name as the name of the current module name
            span.name = '[{}]{}'.format(
                flask.request.method,
                flask.request.url)
            tracer.add_attribute_to_current_span(
                HTTP_METHOD, flask.request.method)
            tracer.add_attribute_to_current_span(HTTP_URL, flask.request.url)
        except Exception:  # pragma: NO COVER
            log.error('Failed to trace request', exc_info=True)

    def _after_request(self, response):
        """A function to be run after each request.

        See: http://flask.pocoo.org/docs/0.12/api/#flask.Flask.after_request
        """
        # Do not trace if the url is blacklisted
        if utils.disable_tracing_url(flask.request.url, self.blacklist_paths):
            return response

        try:
            tracer = execution_context.get_opencensus_tracer()
            tracer.add_attribute_to_current_span(
                HTTP_STATUS_CODE,
                str(response.status_code))
        except Exception:  # pragma: NO COVER
            log.error('Failed to trace request', exc_info=True)
        finally:
            return response

    def _teardown_request(self, exception):
        # Do not trace if the url is blacklisted
        if utils.disable_tracing_url(flask.request.url, self.blacklist_paths):
            return

        try:
            tracer = execution_context.get_opencensus_tracer()

            if exception is not None:
                span = execution_context.get_current_span()
                span.status = status.Status(
                    code=code_pb2.UNKNOWN,
                    message=str(exception)
                )
                # try attaching the stack trace to the span, only populated if
                # the app has 'PROPAGATE_EXCEPTIONS', 'DEBUG', or 'TESTING'
                # enabled
                exc_type, _, exc_traceback = sys.exc_info()
                if exc_traceback is not None:
                    span.stack_trace = stack_trace.StackTrace.from_traceback(
                        exc_traceback
                    )

            tracer.end_span()
            tracer.finish()
        except Exception:  # pragma: NO COVER
            log.error('Failed to trace request', exc_info=True)


def get_flask_header():
    """Get trace context header from flask request headers.

    :rtype: str
    :returns: Trace context header in HTTP request headers.
    """
    header = flask.request.headers.get(_FLASK_TRACE_HEADER)

    # In case the header is unicode, convert it to string.
    if header is not None:
        header = str(header.encode('utf-8'))

    return header
