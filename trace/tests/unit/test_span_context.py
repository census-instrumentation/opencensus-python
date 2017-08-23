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


class TestSpanContext(unittest.TestCase):

    project = 'PROJECT'

    @staticmethod
    def _get_target_class():
        from opencensus.trace.span_context import SpanContext

        return SpanContext

    def _make_one(self, *args, **kw):
        return self._get_target_class()(*args, **kw)

    def test_constructor(self):
        trace_id = '6e0c63257de34c92bf9efcd03927272e'
        span_id = 1234

        span_context = self._make_one(trace_id=trace_id, span_id=span_id)

        self.assertEqual(span_context.trace_id, trace_id)
        self.assertEqual(span_context.span_id, span_id)

    def test__str__(self):
        trace_id = '6e0c63257de34c92bf9efcd03927272e'
        span_id = 1234

        span_context = self._make_one(
            trace_id=trace_id,
            span_id=span_id,
            enabled=True)

        header_expected = '6e0c63257de34c92bf9efcd03927272e/1234;o=1'
        header = span_context.__str__()

        self.assertEqual(header_expected, header)

    def test_check_span_id_none(self):
        span_context = self._make_one(from_header=True)
        span_id = span_context.check_span_id(None)
        self.assertIsNone(span_id)

    def test_check_span_id_zero(self):
        span_context = self._make_one(from_header=True)
        span_id = span_context.check_span_id(0)
        self.assertFalse(span_context.from_header)
        self.assertIsNone(span_id)

    def test_check_span_id_not_int(self):
        span_id = {}
        span_context = self._make_one()
        span_id_checked = span_context.check_span_id(span_id)
        self.assertIsNone(span_id_checked)
        self.assertFalse(span_context.from_header)

    def test_check_span_id_valid(self):
        span_id = 1234
        span_context = self._make_one(from_header=True)
        span_id_checked = span_context.check_span_id(span_id)
        self.assertEqual(span_id, span_id_checked)

    def test_check_trace_id_invalid(self):
        from opencensus.trace.span_context import _INVALID_TRACE_ID

        span_context = self._make_one(from_header=True)

        trace_id_checked = span_context.check_trace_id(_INVALID_TRACE_ID)

        self.assertFalse(span_context.from_header)
        self.assertNotEqual(trace_id_checked, _INVALID_TRACE_ID)

    def test_check_trace_id_not_match(self):
        trace_id_test = 'test_trace_id'

        span_context = self._make_one(from_header=True)
        trace_id_checked = span_context.check_trace_id(trace_id_test)

        self.assertFalse(span_context.from_header)
        self.assertNotEqual(trace_id_checked, trace_id_test)

    def test_check_trace_id_match(self):
        trace_id = '6e0c63257de34c92bf9efcd03927272e'

        span_context = self._make_one(from_header=True)
        trace_id_checked = span_context.check_trace_id(trace_id)

        self.assertEqual(trace_id, trace_id_checked)
        self.assertTrue(span_context.from_header)
