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

_TRACE_CONTEXT_HEADER_FORMAT = \
    '([0-9a-f]{2})(-([0-9a-f]{32}))(-([0-9a-f]{16}))?(-([0-9a-f]{2}))?'
_TRACE_CONTEXT_HEADER_RE = re.compile(_TRACE_CONTEXT_HEADER_FORMAT)


class TraceContextPropagator(object):
    """Propagator for processing the trace context HTTP header format."""

    def from_header(self, header):
        """Generate a SpanContext object using the trace context header.

        :type header: str
        :param header: Trace context header which was extracted from the HTTP
                       request headers.

        :rtype: :class:`~opencensus.trace.span_context.SpanContext`
        :returns: SpanContext generated from the trace context header.
        """
        if header is None:
            return SpanContext()

        try:
            match = re.search(_TRACE_CONTEXT_HEADER_RE, header)
        except TypeError:
            logging.warning(
                'Header should be str, got {}. Cannot parse the header.'
                .format(header.__class__.__name__))
            raise

        if match:
            version = match.group(1)

            if version == '00':
                trace_id = match.group(3)
                span_id = match.group(5)
                trace_options = match.group(7)

                if trace_options is None:
                    trace_options = 1

                # Need to convert span_id from hex string to int
                span_context = SpanContext(
                    trace_id=trace_id,
                    span_id=int(span_id, 16),
                    trace_options=TraceOptions(trace_options),
                    from_header=True)
                return span_context
            else:
                logging.warning(
                    'Header format version {} is not supported, generate a new'
                    'context instead.'.format(version))
        else:
            logging.warning(
                'Cannot parse the header {}, generate a new context instead.'
                .format(header))

        return SpanContext()

    def to_header(self, span_context):
        """Convert a SpanContext object to header string, using version 0.

        :type span_context:
            :class:`~opencensus.trace.span_context.SpanContext`
        :param span_context: SpanContext object.

        :rtype: str
        :returns: A trace context header string in trace context HTTP format.
        """
        trace_id = span_context.trace_id
        span_id = span_context.span_id
        trace_options = span_context.trace_options.enabled

        # Need to convert span_id from int to hex string
        span_id_hex = hex(span_id)
        span_id = span_id_hex[2:].zfill(16)

        # Convert the trace options
        trace_options = '01' if trace_options else '00'

        header = '00-{}-{}-{}'.format(
            trace_id,
            span_id,
            trace_options)
        return header
