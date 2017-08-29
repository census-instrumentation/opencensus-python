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

import unittest

import mock

from opencensus.trace.propagation import binary_format


class TestBinaryFormat(unittest.TestCase):

    def test_from_header_wrong_format(self):
        binary_header = b'\x00\x00\xa0\xb7,\xa1\\\x1aK\xd1\x89b\xd0' \
                        b'\xacY\xdc\x90\xb9\x01g)U\xf6\xf5\x01\x12'

        propagator = binary_format.BinaryFormatPropagator()
        span_context = propagator.from_header(binary_header)

        self.assertFalse(span_context.from_header)

    def test_from_header(self):
        binary_header = b'\x00\x00\xa0\xb7,\xa1\\\x1aK\xd1\x89b\xd0' \
                        b'\xacY\xdc\x90\xb9\x01g)U\xf6\xf5\x01\x12' \
                        b'\xb6\x02\x01'

        expected_trace_id = 'a0b72ca15c1a4bd18962d0ac59dc90b9'
        expected_span_id = 7433567179112518326
        expected_trace_option = True

        propagator = binary_format.BinaryFormatPropagator()

        span_context = propagator.from_header(binary_header)

        self.assertEqual(span_context.trace_id, expected_trace_id)
        self.assertEqual(span_context.span_id, expected_span_id)
        self.assertEqual(span_context.enabled, expected_trace_option)

    def test_to_header_span_id_zero(self):
        from opencensus.trace.span_context import SpanContext

        span_context = mock.Mock(spec=SpanContext)
        trace_id = 'a0b72ca15c1a4bd18962d0ac59dc90b9'
        span_id = None
        enabled = True
        span_context.trace_id = trace_id
        span_context.span_id = span_id
        span_context.enabled = enabled

        propagator = binary_format.BinaryFormatPropagator()

        binary_header = propagator.to_header(span_context)

        expected_binary_header = b'\x00\x00\xa0\xb7,\xa1\\\x1aK\xd1\x89b\xd0' \
                                 b'\xacY\xdc\x90\xb9\x01\x00\x00\x00\x00\x00' \
                                 b'\x00\x00\x00\x02\x01'

        self.assertEqual(expected_binary_header, binary_header)

    def test_to_header(self):
        from opencensus.trace.span_context import SpanContext

        span_context = mock.Mock(spec=SpanContext)
        trace_id = 'a0b72ca15c1a4bd18962d0ac59dc90b9'
        span_id = 7433567179112518326
        enabled = True
        span_context.trace_id = trace_id
        span_context.span_id = span_id
        span_context.enabled = enabled

        propagator = binary_format.BinaryFormatPropagator()

        binary_header = propagator.to_header(span_context)

        expected_binary_header = b'\x00\x00\xa0\xb7,\xa1\\\x1aK\xd1\x89b\xd0' \
                                 b'\xacY\xdc\x90\xb9\x01g)U\xf6\xf5\x01\x12' \
                                 b'\xb6\x02\x01'

        self.assertEqual(expected_binary_header, binary_header)
