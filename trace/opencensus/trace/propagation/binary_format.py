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

import struct

from collections import namedtuple

from opencensus.trace.span_context import SpanContext

_ENABLED_BITMASK = 1

UTF8 = 'utf-8'

VERSION_ID = 0
TRACE_ID_FIELD_ID = 0
SPAN_ID_FIELD_ID = 1
TRACE_OPTION_FIELD_ID = 2

ID_SIZE = 1
TRACE_ID_SIZE = 32
SPAN_ID_SIZE = 16
TRACE_OPTION_SIZE = 1

FORMAT_LENGTH = 4 * ID_SIZE + TRACE_ID_SIZE + SPAN_ID_SIZE + TRACE_OPTION_SIZE

# See: https://docs.python.org/3/library/struct.html#format-characters
INT_FORMAT = 'i'
CHAR_ARRAY_FORMAT = 's'

BINARY_FORMAT = '{version_id}' \
    '{trace_id_field_id}{trace_id}' \
    '{span_id_field_id}{span_id}' \
    '{trace_option_field_id}{trace_option}'\
        .format(
            version_id='{}{}'.format(ID_SIZE, INT_FORMAT),
            trace_id_field_id='{}{}'.format(ID_SIZE, INT_FORMAT),
            trace_id='{}{}'.format(TRACE_ID_SIZE, CHAR_ARRAY_FORMAT),
            span_id_field_id='{}{}'.format(ID_SIZE, INT_FORMAT),
            span_id='{}{}'.format(SPAN_ID_SIZE, CHAR_ARRAY_FORMAT),
            trace_option_field_id='{}{}'.format(ID_SIZE, INT_FORMAT),
            trace_option='{}{}'.format(TRACE_OPTION_SIZE, CHAR_ARRAY_FORMAT)
        )

Header = namedtuple(
    'Header',
    'version_id '
    'trace_id_field_id '
    'trace_id '
    'span_id_field_id '
    'span_id '
    'trace_option_field_id '
    'trace_option')


class BinaryFormatPropagator(object):
    """This propagator contains the method for serializing and deserializing
    SpanContext using a binary format.
    
    See: https://github.com/census-instrumentation/opencensus-specs/blob/
         master/encodings/BinaryEncoding.md
    """
    def from_header(self, binary):
        """Generate a SpanContext object using the trace context header.
        The value of enabled parsed from header is int. Need to convert to
        bool.

        :type binary: bytes
        :param binary: Trace context header which was extracted from the
                       request headers.

        :rtype: :class:`~opencensus.trace.span_context.SpanContext`
        :returns: SpanContext generated from the trace context header.
        """

        data = Header._make(struct.unpack(BINARY_FORMAT, binary))
        trace_id = data.trace_id.decode(UTF8)
        span_id = data.span_id.decode(UTF8)
        trace_option = data.trace_option.decode(UTF8)

        enabled = bool(int(trace_option) & _ENABLED_BITMASK)

        span_context = SpanContext(
                trace_id=trace_id,
                span_id=span_id,
                enabled=enabled,
                from_header=True)

        return span_context

    def to_header(self, span_context):
        """Convert a SpanContext object to header in binary format.
        
        :type span_context:
            :class:`~opencensus.trace.span_context.SpanContext`
        :param span_context: SpanContext object.
        
        :rtype: bytes
        :returns: A trace context header in binary format.
        """
        trace_id = span_context.trace_id
        span_id = span_context.span_id
        enabled = span_context.enabled

        # Pad zeroes to span_id if length less than 16
        span_id_str = str(span_id).zfill(16)

        enabled_str = str(enabled)

        return struct.pack(
            BINARY_FORMAT,
            0,
            0,
            bytes(trace_id, UTF8),
            1,
            bytes(span_id_str, UTF8),
            2,
            bytes(enabled_str, UTF8))
