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


class TestTrace(unittest.TestCase):

    @staticmethod
    def _get_target_class():
        from opencensus.trace.trace import Trace

        return Trace

    def _make_one(self, *args, **kw):
        return self._get_target_class()(*args, **kw)

    def test_constructor_defaults(self):
        trace_id = 'test_trace_id'

        patch = mock.patch(
            'opencensus.trace.trace.generate_trace_id',
            return_value=trace_id)

        with patch:
            trace = self._make_one()

        self.assertEqual(trace.trace_id, trace_id)

    def test_constructor_explicit(self):
        trace_id = 'test_trace_id'

        trace = self._make_one(trace_id=trace_id)

        self.assertEqual(trace.trace_id, trace_id)

    def test_start(self):
        trace = self._make_one()
        trace.start()

        self.assertEqual(trace.spans, [])

    def test_finish(self):
        from opencensus.trace.enums import Enum
        from opencensus.trace.trace_span import TraceSpan

        trace = self._make_one()

        span_name = 'span'
        span_id = 123
        kind = Enum.SpanKind.SPAN_KIND_UNSPECIFIED
        start_time = '2017-06-25'
        end_time = '2017-06-26'

        span = mock.Mock(spec=TraceSpan)
        span.name = span_name
        span.kind = kind
        span.parent_span_id = None
        span.span_id = span_id
        span.start_time = start_time
        span.end_time = end_time
        span.labels = None
        span.children = []
        span.__iter__ = mock.Mock(return_value=iter([span]))

        with trace:
            trace.spans = [span]
            self.assertEqual(trace.spans, [span])

        self.assertEqual(trace.spans, [])

    def test_span(self):
        from opencensus.trace.trace_span import TraceSpan

        span_name = 'test_span_name'

        trace = self._make_one()
        trace.spans = []

        trace.span(name=span_name)
        self.assertEqual(len(trace.spans), 1)

        result_span = trace.spans[0]
        self.assertIsInstance(result_span, TraceSpan)
        self.assertEqual(result_span.name, span_name)
