# Copyright 2017 Google Inc. All Rights Reserved.
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

class Test_from_carrier(unittest.TestCase):

    def test_from_carrier_keys_exist(self):
        from opencensus.trace.propagation import text_format

        test_trace_id = '6e0c63257de34c92bf9efcd03927272e'
        test_span_id = 1234
        test_options = 1

        carrier = {
            text_format._TRACE_ID_KEY: test_trace_id,
            text_format._SPAN_ID_KEY: test_span_id,
            text_format._ENABLED_TRACE_KEY: test_options,
        }

        span_context = text_format.from_carrier(carrier)

        self.assertEqual(span_context.trace_id, test_trace_id)
        self.assertEqual(span_context.span_id, test_span_id)
        self.assertEqual(span_context.enabled, bool(test_options))

    def test_from_carrier_keys_not_exist(self):
        from opencensus.trace.propagation import text_format

        carrier = {}

        span_context = text_format.from_carrier(carrier)

        self.assertIsNotNone(span_context.trace_id)
        # Span_id should be None here which indicates no parent span_id for
        # the child spans
        self.assertIsNone(span_context.span_id)
        self.assertTrue(span_context.enabled)

    def test_to_carrier_has_span_id(self):
        from opencensus.trace.propagation import text_format

        test_trace_id = '6e0c63257de34c92bf9efcd03927272e'
        test_span_id = 1234
        test_options = 1

        span_context = mock.Mock()
        span_context.trace_id = test_trace_id
        span_context.span_id = test_span_id
        span_context.enabled = bool(test_options)

        carrier = {}
        carrier = text_format.to_carrier(span_context, carrier)

        self.assertEqual(
            carrier[text_format._TRACE_ID_KEY],
            test_trace_id)
        self.assertEqual(
            carrier[text_format._SPAN_ID_KEY],
            str(test_span_id))
        self.assertEqual(
            carrier[text_format._ENABLED_TRACE_KEY],
            str(bool(test_options)))

    def test_to_carrier_no_span_id(self):
        from opencensus.trace.propagation import text_format

        test_trace_id = '6e0c63257de34c92bf9efcd03927272e'
        test_options = 1

        span_context = mock.Mock()
        span_context.trace_id = test_trace_id
        span_context.span_id = None
        span_context.enabled = bool(test_options)

        carrier = {}
        carrier = text_format.to_carrier(span_context, carrier)

        self.assertEqual(
            carrier[text_format._TRACE_ID_KEY],
            test_trace_id)
        self.assertIsNone(
            carrier.get(text_format._SPAN_ID_KEY))
        self.assertEqual(
            carrier[text_format._ENABLED_TRACE_KEY],
            str(bool(test_options)))
