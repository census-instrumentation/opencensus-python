# Copyright 2018, OpenCensus Authors
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


from opencensus.trace.span_context import SpanContext, INVALID_SPAN_ID
from opencensus.trace.trace_options import TraceOptions

_TRACE_ID_KEY = 'x-b3-traceid'
_SPAN_ID_KEY = 'x-b3-spanid'
_SAMPLED_KEY = 'x-b3-sampled'


class B3FormatPropagator(object):
    """Propagator for processing the B3 HTTP header format.

    See: https://github.com/openzipkin/b3-propagation
    """

    def from_headers(self, headers):
        """Generate a SpanContext object using the trace context headers.

        :type headers: dict
        :param headers: HTTP request headers.

        :rtype: :class:`~opencensus.trace.span_context.SpanContext`
        :returns: SpanContext generated from the trace context header.
        """
        if headers is None:
            return SpanContext(from_header=False)

        trace_id = headers.get(_TRACE_ID_KEY)
        span_id = headers.get(_SPAN_ID_KEY)
        sampled = headers.get(_SAMPLED_KEY) == '1'

        # Trace Id and Span Id headers both have to exist
        if not trace_id or not span_id:
            return SpanContext()

        # Convert 64-bit trace ids to 128-bit
        if len(trace_id) == 16:
            trace_id = '0'*16 + trace_id

        trace_options = TraceOptions()
        trace_options.set_enabled(sampled)

        span_context = SpanContext(
            trace_id=trace_id,
            span_id=span_id,
            trace_options=trace_options,
            from_header=True
        )

        return span_context

    def to_headers(self, span_context):
        """Convert a SpanContext object to HTTP request headers.

        :type span_context:
            :class:`~opencensus.trace.span_context.SpanContext`
        :param span_context: SpanContext object.

        :rtype: dict
        :returns: Trace context headers in B3 propagation format.
        """

        if not span_context.span_id:
            span_id = INVALID_SPAN_ID
        else:
            span_id = span_context.span_id

        sampled = span_context.trace_options.get_enabled()

        return {
            _TRACE_ID_KEY: span_context.trace_id,
            _SPAN_ID_KEY: span_id,
            _SAMPLED_KEY: '1' if sampled else '0'
        }
