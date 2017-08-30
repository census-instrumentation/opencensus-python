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

"""The WebApp2Tracer maintains the trace spans for a trace in webapp2
application.

Note: webapp2 is only supported in Python2.
"""

try:
    import webapp2
except (ImportError, SyntaxError):  # pragma: NO COVER
    webapp2 = None

from opencensus.trace.request_tracer import RequestTracer
from opencensus.trace.propagation import google_cloud_format

_WEBAPP2_TRACE_KEY = 'X-CLOUD-TRACE-CONTEXT'


class WebApp2Tracer(RequestTracer):
    """The WebApp2 implementation of the ContextTracer Interface.

    :type span_context: :class:`~opencensus.trace.span_context.SpanContext`
    :param span_context: The current span context.

    :type sampler: :class:`type`
    :param sampler: Class for creating new Sampler objects. It should extend
                    from the base :class:`.Sampler` type and implement
                    :meth:`.Sampler.should_sample`. Defaults to
                    :class:`.AlwaysOnSampler`. The rest options are
                    :class:`.AlwaysOffSampler`, :class:`.FixedRateSampler`.

    :type reporter: :class:`type`
    :param reporter: Class for creating new Reporter objects. Default to
                     :class:`.PrintReporter`. The rest option is
                     :class:`.FileReporter`.
    """
    def __init__(
            self,
            span_context=None,
            sampler=None,
            reporter=None,
            propagator=None):
        if propagator is None:
            propagator = google_cloud_format.GoogleCloudFormatPropagator()

        if span_context is None:
            header = get_webapp2_header()
            span_context = propagator.from_header(header)

        super(WebApp2Tracer, self).__init__(
            span_context=span_context,
            sampler=sampler,
            reporter=reporter,
            propagator=propagator)


def get_webapp2_header():
    """Get trace context header from webapp2 request headers.

    :rtype: str
    :returns: Trace context header in HTTP request headers.
    """
    if webapp2 is None:  # pragma: NO COVER
        return None

    try:
        request = webapp2.get_request()
    except AssertionError:
        return None

    header = request.headers.get(_WEBAPP2_TRACE_KEY)

    return header
