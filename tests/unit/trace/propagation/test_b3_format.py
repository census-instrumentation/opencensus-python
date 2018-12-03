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

import unittest
import mock

from opencensus.trace.span_context import INVALID_SPAN_ID
from opencensus.trace.propagation import b3_format


class TestB3FormatPropagator(unittest.TestCase):

    def test_from_headers_no_headers(self):
        propagator = b3_format.B3FormatPropagator()
        span_context = propagator.from_headers(None)

        self.assertFalse(span_context.from_header)

    def test_from_headers_keys_exist(self):
        test_trace_id = '6e0c63257de34c92bf9efcd03927272e'
        test_span_id = '00f067aa0ba902b7'
        test_sampled = '1'

        headers = {
            b3_format._TRACE_ID_KEY: test_trace_id,
            b3_format._SPAN_ID_KEY: test_span_id,
            b3_format._SAMPLED_KEY: test_sampled,
        }

        propagator = b3_format.B3FormatPropagator()
        span_context = propagator.from_headers(headers)

        self.assertEqual(span_context.trace_id, test_trace_id)
        self.assertEqual(span_context.span_id, test_span_id)
        self.assertEqual(
            span_context.trace_options.enabled,
            bool(test_sampled)
        )

    def test_from_headers_keys_not_exist(self):
        propagator = b3_format.B3FormatPropagator()
        span_context = propagator.from_headers({})

        self.assertIsNotNone(span_context.trace_id)
        self.assertIsNone(span_context.span_id)
        self.assertFalse(span_context.trace_options.enabled)

    def test_from_headers_64bit_traceid(self):
        test_trace_id = 'bf9efcd03927272e'
        test_span_id = '00f067aa0ba902b7'

        headers = {
            b3_format._TRACE_ID_KEY: test_trace_id,
            b3_format._SPAN_ID_KEY: test_span_id,
        }

        propagator = b3_format.B3FormatPropagator()
        span_context = propagator.from_headers(headers)

        converted_trace_id = "0"*16 + test_trace_id

        self.assertEqual(span_context.trace_id, converted_trace_id)
        self.assertEqual(span_context.span_id, test_span_id)

    def test_to_headers_has_span_id(self):
        test_trace_id = '6e0c63257de34c92bf9efcd03927272e'
        test_span_id = '00f067aa0ba902b7'
        test_options = '1'

        span_context = mock.Mock()
        span_context.trace_id = test_trace_id
        span_context.span_id = test_span_id
        span_context.trace_options.trace_options_byte = test_options

        propagator = b3_format.B3FormatPropagator()
        headers = propagator.to_headers(span_context)

        self.assertEqual(headers[b3_format._TRACE_ID_KEY], test_trace_id)
        self.assertEqual(headers[b3_format._SPAN_ID_KEY], test_span_id)
        self.assertEqual(headers[b3_format._SAMPLED_KEY], test_options)

    def test_to_headers_no_span_id(self):
        test_trace_id = '6e0c63257de34c92bf9efcd03927272e'
        test_options = '1'

        span_context = mock.Mock()
        span_context.trace_id = test_trace_id
        span_context.span_id = None
        span_context.trace_options.trace_options_byte = test_options

        propagator = b3_format.B3FormatPropagator()
        headers = propagator.to_headers(span_context)

        self.assertEqual(headers[b3_format._TRACE_ID_KEY], test_trace_id)
        self.assertEqual(headers.get(b3_format._SPAN_ID_KEY), INVALID_SPAN_ID)
        self.assertEqual(headers[b3_format._SAMPLED_KEY], test_options)

    def test_from_single_header_keys_exist(self):
        trace_id = "80f198ee56343ba864fe8b2a57d3eff7"
        span_id = "e457b5a2e4d86bd1"

        headers = {
            'b3': "{}-{}-d-05e3ac9a4f6e3b90".format(trace_id, span_id)
        }
        propagator = b3_format.B3FormatPropagator()
        span_context = propagator.from_headers(headers)

        self.assertEqual(span_context.trace_id, trace_id)
        self.assertEqual(span_context.span_id, span_id)
        self.assertEqual(span_context.trace_options.enabled, True)

    def test_from_headers_invalid_single_header(self):
        headers = {
            'b3': "01234567890123456789012345678901;o=1"
        }
        propagator = b3_format.B3FormatPropagator()
        span_context = propagator.from_headers(headers)

        self.assertFalse(span_context.from_header)

    def test_from_headers_invalid_single_header_fields(self):
        headers = {
            'b3': "a-b-c-d-e-f-g"
        }
        propagator = b3_format.B3FormatPropagator()
        span_context = propagator.from_headers(headers)

        self.assertFalse(span_context.from_header)

    def test_from_single_header_deny_sampling(self):
        headers = {
            'b3': "0"
        }
        propagator = b3_format.B3FormatPropagator()
        span_context = propagator.from_headers(headers)

        self.assertEqual(span_context.trace_options.enabled, False)

    def test_from_single_header_defer_sampling(self):
        trace_id = "80f198ee56343ba864fe8b2a57d3eff7"
        span_id = "e457b5a2e4d86bd1"
        headers = {
            'b3': "{}-{}".format(trace_id, span_id)
        }
        propagator = b3_format.B3FormatPropagator()
        span_context = propagator.from_headers(headers)

        self.assertEqual(span_context.trace_id, trace_id)
        self.assertEqual(span_context.span_id, span_id)

    def test_from_single_header_precedence(self):
        headers = {
            'b3': "80f198ee56343ba864fe8b2a57d3eff7-e457b5a2e4d86bd1-1",
            'X-B3-TraceId': '6e0c63257de34c92bf9efcd03927272e',
            'X-B3-SpanId': '00f067aa0ba902b7'
        }
        propagator = b3_format.B3FormatPropagator()
        span_context = propagator.from_headers(headers)

        self.assertEqual(
            span_context.trace_id,
            "80f198ee56343ba864fe8b2a57d3eff7"
        )
        self.assertEqual(span_context.span_id, "e457b5a2e4d86bd1")
        self.assertEqual(span_context.trace_options.enabled, True)
