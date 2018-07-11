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
import re

from opencensus.trace.span_context import SpanContext
from opencensus.trace.trace_options import TraceOptions

_UBER_HEADER_NAME = 'UBER_TRACE_ID'
_UBER_HEADER_FORMAT = ('([0-9a-f]{0,32}|)\:([0-9a-f]{0,16})\:'
                       '([0-9a-f]{0,16}|)\:([0-9a-f]{1,2})')
_UBER_HEADER_RE = re.compile(_UBER_HEADER_FORMAT)


class JaegerFormatPropagator(object):
    """This class is for converting the trace header in Jaeger's format
    and generate a SpanContext, or converting a SpanContext to Jaeger's trace
    header.
    """
    def from_header(self, header):
        """Generate a SpanContext object using the trace context header.
        The value of enabled parsed from header is int. Need to convert to
        bool.

        :type header: str
        :param header: Trace context header which was extracted from the HTTP
                       request headers.

        :rtype: :class:`~opencensus.trace.span_context.SpanContext`
        :returns: SpanContext generated from the trace context header.
        """
        if header is None:
            return SpanContext()

        try:
            match = re.search(_UBER_HEADER_RE, header)
        except TypeError:
            logging.warning(
                'Header should be str, got {}. Cannot parse the header.'
                .format(header.__class__.__name__))
            raise

        if match:
            trace_id = match.group(1)
            span_id = match.group(2)
            trace_options = match.group(4)

            span_context = SpanContext(
                trace_id=trace_id,
                span_id=span_id,
                trace_options=TraceOptions(str(int('0x' + trace_options, 16))),
                from_header=True)
            return span_context
        else:
            logging.warning(
                'Cannot parse the header {}, generate a new context instead.'
                .format(header))
            return SpanContext()

    def from_headers(self, headers):
        """Generate a SpanContext object using the trace context header.

        :type headers: dict
        :param headers: HTTP request headers.

        :rtype: :class:`~opencensus.trace.span_context.SpanContext`
        :returns: SpanContext generated from the trace context header.
        """
        if headers is None:
            return SpanContext()
        if _UBER_HEADER_NAME not in headers:
            return SpanContext()
        return self.from_header(headers[_UBER_HEADER_NAME])

    def to_header(self, span_context):
        """Convert a SpanContext object to header string.

        :type span_context:
            :class:`~opencensus.trace.span_context.SpanContext`
        :param span_context: SpanContext object.

        :rtype: str
        :returns: A trace context header string in google cloud format.
        """
        trace_id = span_context.trace_id
        span_id = span_context.span_id
        trace_options = span_context.trace_options.trace_options_byte

        header = '{}:{}::{:02x}'.format(
            trace_id,
            span_id,
            int(trace_options))
        return header

    def to_headers(self, span_context):
        """Convert a SpanContext object to HTTP request headers.

        :type span_context:
            :class:`~opencensus.trace.span_context.SpanContext`
        :param span_context: SpanContext object.

        :rtype: dict
        :returns: Trace context headers in google cloud format.
        """
        return {
            _UBER_HEADER_NAME: self.to_header(span_context),
        }
