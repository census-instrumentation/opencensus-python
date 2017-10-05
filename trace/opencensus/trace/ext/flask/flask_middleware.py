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
from opencensus.trace import execution_context
from opencensus.trace.propagation import google_cloud_format
from opencensus.trace.reporters import print_reporter
from opencensus.trace.samplers import always_on
from opencensus.trace import request_tracer

_FLASK_TRACE_HEADER = 'X_CLOUD_TRACE_CONTEXT'

HTTP_METHOD = labels_helper.STACKDRIVER_LABELS['HTTP_METHOD']
HTTP_URL = labels_helper.STACKDRIVER_LABELS['HTTP_URL']
HTTP_STATUS_CODE = labels_helper.STACKDRIVER_LABELS['HTTP_STATUS_CODE']

log = logging.getLogger(__name__)


class FlaskMiddleware(object):
    """Flask middleware to automatically trace requests.

    :type app: :class: `~flask.Flask`
    :param app: A flask application.

    :type sampler: :class: `type`
    :param sampler: Class for creating new Sampler objects. It should extend
                    from the base :class:`.Sampler` type and implement
                    :meth:`.Sampler.should_sample`. Defaults to
                    :class:`.AlwaysOnSampler`. The rest options are
                    :class:`.AlwaysOffSampler`, :class:`.FixedRateSampler`.

    :type reporter: :class: `type`
    :param reporter: Class for creating new Reporter objects. Default to
                     :class:`.PrintReporter`. The rest option is
                     :class:`.FileReporter`.
    """
    def __init__(self, app, sampler=None, reporter=None, propagator=None):
        if sampler is None:
            sampler = always_on.AlwaysOnSampler()

        if reporter is None:
            reporter = print_reporter.PrintReporter()

        if propagator is None:
            propagator = google_cloud_format.GoogleCloudFormatPropagator()

        self.app = app
        self.sampler = sampler
        self.reporter = reporter
        self.propagator = propagator
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
            span_context = self.propagator.from_header(header)

            tracer = request_tracer.RequestTracer(
                span_context=span_context,
                sampler=self.sampler,
                reporter=self.reporter,
                propagator=self.propagator)

            tracer.start_trace()

            span = tracer.start_span()

            # Set the span name as the name of the current module name
            span.name = '[{}]{}'.format(
                flask.request.method,
                flask.request.url)
            tracer.add_label_to_spans(HTTP_METHOD, flask.request.method)
            tracer.add_label_to_spans(HTTP_URL, flask.request.url)
        except Exception:  # pragma: NO COVER
            log.error('Failed to trace request', exc_info=True)

    def _after_request(self, response):
        """A function to be run after each request.

        See: http://flask.pocoo.org/docs/0.12/api/#flask.Flask.after_request
        """
        try:
            tracer = execution_context.get_opencensus_tracer()
            tracer.add_label_to_spans(
                HTTP_STATUS_CODE,
                str(response.status_code))

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

    # In case the header is unicode, convert it to string.
    if header is not None:
        header = str(header.encode('utf-8'))

    return header
