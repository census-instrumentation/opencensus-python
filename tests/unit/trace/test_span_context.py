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
from opencensus.trace import span_context as span_context_module
from opencensus.trace.trace_options import TraceOptions
from opencensus.trace.tracestate import Tracestate


class TestSpanContext(unittest.TestCase):
    project = 'PROJECT'
    trace_id = '6e0c63257de34c92bf9efcd03927272e'
    span_id = '6e0c63257de34c92'

    @staticmethod
    def _get_target_class():
        return span_context_module.SpanContext

    def _make_one(self, *args, **kw):
        return self._get_target_class()(*args, **kw)

    def test_constructor(self):
        span_context = self._make_one(
            trace_id=self.trace_id, span_id=self.span_id)

        self.assertEqual(span_context.trace_id, self.trace_id)
        self.assertEqual(span_context.span_id, self.span_id)

    def test__repr__(self):
        span_context = self._make_one(
            trace_id=self.trace_id,
            span_id=self.span_id,
            trace_options=TraceOptions('1'),
            tracestate=Tracestate())

        expected_repr = ('SpanContext('
                         'trace_id=6e0c63257de34c92bf9efcd03927272e, '
                         'span_id=6e0c63257de34c92, '
                         'trace_options=TraceOptions(enabled=True), '
                         'tracestate=Tracestate())')

        self.assertEqual(expected_repr, span_context.__repr__())

    def test_check_span_id_none(self):
        span_context = self._make_one(trace_id=self.trace_id, from_header=True)
        self.assertIsNone(span_context.span_id)

    def test_check_span_id_zero(self):
        span_context = self._make_one(
            from_header=True,
            trace_id=self.trace_id,
            span_id=span_context_module.INVALID_SPAN_ID)
        self.assertFalse(span_context.from_header)
        self.assertIsNone(span_context.span_id)

    def test_check_span_id_not_str(self):
        with self.assertRaises(AssertionError):
            self._make_one(
                from_header=True, trace_id=self.trace_id, span_id={})

    def test_check_span_id_valid(self):
        span_context = self._make_one(
            from_header=True, trace_id=self.trace_id, span_id=self.span_id)
        self.assertEqual(span_context.span_id, self.span_id)

    def test_check_trace_id_invalid(self):
        span_context = self._make_one(
            from_header=True,
            trace_id=span_context_module._INVALID_TRACE_ID,
            span_id=self.span_id)

        self.assertFalse(span_context.from_header)
        self.assertNotEqual(span_context.trace_id,
                            span_context_module._INVALID_TRACE_ID)

    def test_check_trace_id_invalid_format(self):
        trace_id_test = 'test_trace_id'
        span_context = self._make_one(
            from_header=True, trace_id=trace_id_test, span_id=self.span_id)

        self.assertFalse(span_context.from_header)
        self.assertNotEqual(span_context.trace_id, trace_id_test)

    def test_check_trace_id_valid_format(self):
        span_context = self._make_one(
            from_header=True, trace_id=self.trace_id, span_id=self.span_id)

        self.assertEqual(span_context.trace_id, self.trace_id)
        self.assertTrue(span_context.from_header)

    def test_check_span_id_invalid_format(self):
        span_id_test = 'test_trace_id'
        span_context = self._make_one(
            from_header=True, trace_id=self.trace_id, span_id=span_id_test)

        self.assertFalse(span_context.from_header)
        self.assertIsNone(span_context.span_id)
