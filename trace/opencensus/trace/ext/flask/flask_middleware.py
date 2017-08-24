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

from opencensus.trace import labels_helper
from opencensus.trace.propagation import google_cloud_format
from opencensus.trace.reporters import print_reporter
from opencensus.trace.samplers import always_on
from opencensus.trace.tracer import context_tracer

_FLASK_TRACE_HEADER = 'X_CLOUD_TRACE_CONTEXT'

HTTP_METHOD = labels_helper.STACKDRIVER_LABELS['HTTP_METHOD']
HTTP_URL = labels_helper.STACKDRIVER_LABELS['HTTP_URL']
HTTP_STATUS_CODE = labels_helper.STACKDRIVER_LABELS['HTTP_STATUS_CODE']

TRACER_KEY = 'tracer'

log = logging.getLogger(__name__)


class FlaskMiddleware(object):
    """Flask middleware to automatically trace requests."""

    def __init__(self, app, sampler=None, reporter=None):
        if sampler is None:
            sampler = always_on.AlwaysOnSampler()

        if reporter is None:
            reporter = print_reporter.PrintReporter()

        self.app = app
        self.sampler = sampler
        self.reporter = reporter
        self.setup_trace()

    def setup_trace(self):
        self.app.before_request(self._before_request)
        self.app.after_request(self._after_request)

    def _before_request(self):
        """A function to be run before each request.

        See: http://flask.pocoo.org/docs/0.12/api/#flask.Flask.before_request
        """
        try:
            header = get_flask_header()
            span_context = google_cloud_format.from_header(header)

            tracer = context_tracer.ContextTracer(
                span_context=span_context,
                sampler=self.sampler,
                reporter=self.reporter)
            tracer.start_trace()

            span = tracer.start_span()

            # Set the span name as the name of the current module name
            span.name = flask.request.module
            span.add_label(HTTP_METHOD, flask.request.method)
            span.add_label(HTTP_URL, flask.request.url)

            # Add tracer to flask application globals
            setattr(flask.g, TRACER_KEY, tracer)
        except Exception:  # pragma: NO COVER
            log.error('Failed to trace request', exc_info=True)


    def _after_request(self, response):
        """A function to be run after each request.

        See: http://flask.pocoo.org/docs/0.12/api/#flask.Flask.after_request
        """
        try:
            tracer = flask.g.get(TRACER_KEY, None)
            span = tracer._span_stack[-1]
            span.add_label(HTTP_STATUS_CODE, response.status_code)

            tracer.end_span()
            tracer.end_trace()
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

    return header
