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

import flask
import logging

from opencensus.trace import attributes_helper
from opencensus.trace import execution_context
from opencensus.trace.propagation import google_cloud_format
from opencensus.trace.exporters import print_exporter
from opencensus.trace.ext import utils
from opencensus.trace.samplers import always_on
from opencensus.trace import tracer as tracer_module

_FLASK_TRACE_HEADER = 'X_CLOUD_TRACE_CONTEXT'

HTTP_METHOD = attributes_helper.COMMON_ATTRIBUTES['HTTP_METHOD']
HTTP_URL = attributes_helper.COMMON_ATTRIBUTES['HTTP_URL']
HTTP_STATUS_CODE = attributes_helper.COMMON_ATTRIBUTES['HTTP_STATUS_CODE']

log = logging.getLogger(__name__)


class FlaskMiddleware(object):
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
    def __init__(self, app, blacklist_paths=None, sampler=None, exporter=None,
                 propagator=None):
        if sampler is None:
            sampler = always_on.AlwaysOnSampler()

        if exporter is None:
            exporter = print_exporter.PrintExporter()

        if propagator is None:
            propagator = google_cloud_format.GoogleCloudFormatPropagator()

        self.app = app
        self.blacklist_paths = blacklist_paths
        self.sampler = sampler
        self.exporter = exporter
        self.propagator = propagator
        self.setup_trace()

    def setup_trace(self):
        self.app.before_request(self._before_request)
        self.app.after_request(self._after_request)

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

            tracer.end_span()
            tracer.finish()
        except Exception:  # pragma: NO COVER
            log.error('Failed to trace request', exc_info=True)
        finally:
            return response


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
