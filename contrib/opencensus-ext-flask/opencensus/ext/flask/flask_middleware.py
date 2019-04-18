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

import logging
import six
import sys

import flask
from google.rpc import code_pb2

from opencensus.common import configuration
from opencensus.trace import attributes_helper
from opencensus.trace import execution_context
from opencensus.trace import print_exporter
from opencensus.trace import span as span_module
from opencensus.trace import stack_trace
from opencensus.trace import status
from opencensus.trace import tracer as tracer_module
from opencensus.trace import utils
from opencensus.trace.propagation import trace_context_http_header_format
from opencensus.trace.samplers import always_on

HTTP_METHOD = attributes_helper.COMMON_ATTRIBUTES['HTTP_METHOD']
HTTP_URL = attributes_helper.COMMON_ATTRIBUTES['HTTP_URL']
HTTP_STATUS_CODE = attributes_helper.COMMON_ATTRIBUTES['HTTP_STATUS_CODE']

BLACKLIST_PATHS = 'BLACKLIST_PATHS'
BLACKLIST_HOSTNAMES = 'BLACKLIST_HOSTNAMES'

log = logging.getLogger(__name__)


class FlaskMiddleware(object):
    """Flask middleware to automatically trace requests.

    :type app: :class: `~flask.Flask`
    :param app: A flask application.

    :type blacklist_paths: list
    :param blacklist_paths: Paths that do not trace.

    :type sampler: :class:`~opencensus.trace.samplers.base.Sampler`
    :param sampler: A sampler. It should extend from the base
                    :class:`.Sampler` type and implement
                    :meth:`.Sampler.should_sample`. Defaults to
                    :class:`.AlwaysOnSampler`. The rest options are
                    :class:`.AlwaysOffSampler`, :class:`.FixedRateSampler`.

    :type exporter: :class:`~opencensus.trace.base_exporter.exporter`
    :param exporter: An exporter. Default to
                     :class:`.PrintExporter`. The rest options are
                     :class:`.FileExporter`, :class:`.LoggingExporter` and
                     trace exporter extensions.

    :type propagator: :class: 'object'
    :param propagator: A propagator. Default to
                       :class:`.TraceContextPropagator`. The rest options
                       are :class:`.BinaryFormatPropagator`,
                       :class:`.GoogleCloudFormatPropagator` and
                       :class:`.TextFormatPropagator`.
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
        settings = self.app.config.get('OPENCENSUS', {})
        settings = settings.get('TRACE', {})

        if self.sampler is None:
            self.sampler = settings.get('SAMPLER', None) or \
                always_on.AlwaysOnSampler()
            if isinstance(self.sampler, six.string_types):
                self.sampler = configuration.load(self.sampler)

        if self.exporter is None:
            self.exporter = settings.get('EXPORTER', None) or \
                print_exporter.PrintExporter()
            if isinstance(self.exporter, six.string_types):
                self.exporter = configuration.load(self.exporter)

        if self.propagator is None:
            self.propagator = settings.get('PROPAGATOR', None) or \
                trace_context_http_header_format.TraceContextPropagator()
            if isinstance(self.propagator, six.string_types):
                self.propagator = configuration.load(self.propagator)

        self.blacklist_paths = settings.get(BLACKLIST_PATHS,
                                            self.blacklist_paths)

        self.blacklist_hostnames = settings.get(BLACKLIST_HOSTNAMES, None)

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
            span_context = self.propagator.from_headers(flask.request.headers)

            tracer = tracer_module.Tracer(
                span_context=span_context,
                sampler=self.sampler,
                exporter=self.exporter,
                propagator=self.propagator)

            span = tracer.start_span()
            span.span_kind = span_module.SpanKind.SERVER
            # Set the span name as the name of the current module name
            span.name = '[{}]{}'.format(
                flask.request.method,
                flask.request.url)
            tracer.add_attribute_to_current_span(
                HTTP_METHOD, flask.request.method)
            tracer.add_attribute_to_current_span(
                HTTP_URL, str(flask.request.url))
            execution_context.set_opencensus_attr(
                'blacklist_hostnames',
                self.blacklist_hostnames)
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
                if span is not None:
                    span.status = status.Status(
                        code=code_pb2.UNKNOWN,
                        message=str(exception)
                    )
                    # try attaching the stack trace to the span, only populated
                    # if the app has 'PROPAGATE_EXCEPTIONS', 'DEBUG', or
                    # 'TESTING' enabled
                    exc_type, _, exc_traceback = sys.exc_info()
                    if exc_traceback is not None:
                        span.stack_trace = (
                            stack_trace.StackTrace.from_traceback(
                                exc_traceback
                            )
                        )

            tracer.end_span()
            tracer.finish()
        except Exception:  # pragma: NO COVER
            log.error('Failed to trace request', exc_info=True)
