# Copyright 2017 Google Inc.
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

    project = 'PROJECT'

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
        reporter = mock.Mock()

        trace = self._make_one(
            project_id=self.project,
            trace_id=trace_id,
            reporter=reporter)

        self.assertEqual(trace.project_id, self.project)
        self.assertEqual(trace.trace_id, trace_id)
        self.assertIs(trace.reporter, reporter)

    def test_start(self):
        trace = self._make_one(project_id=self.project)
        trace.start()

        self.assertEqual(trace.spans, [])

    def test_finish_with_valid_span(self):
        from opencensus.trace.enums import Enum
        from opencensus.trace.trace_span import TraceSpan

        reporter = mock.Mock()
        trace = self._make_one(reporter=reporter)

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

        trace = self._make_one(project_id=self.project)
        trace.spans = []

        trace.span(name=span_name)
        self.assertEqual(len(trace.spans), 1)

        result_span = trace.spans[0]
        self.assertIsInstance(result_span, TraceSpan)
        self.assertEqual(result_span.name, span_name)

    def test_send_without_spans(self):
        trace_id = 'test_trace_id'
        reporter = mock.Mock()
        trace = self._make_one(
            project_id=self.project,
            trace_id=trace_id,
            reporter=reporter)
        trace.spans = []

        trace.send()

        self.assertFalse(reporter.called)
        self.assertEqual(trace.project_id, self.project)
        self.assertEqual(trace.trace_id, trace_id)
        self.assertEqual(trace.spans, [])

    def test_send_with_spans(self):
        from opencensus.trace.enums import Enum
        from opencensus.trace.trace_span import TraceSpan

        trace_id = 'test_trace_id'
        reporter = mock.Mock()
        trace = self._make_one(
            project_id=self.project,
            trace_id=trace_id,
            reporter=reporter)
        child_span_name = 'child_span'
        root_span_name = 'root_span'
        child_span_id = 123
        root_span_id = 456
        kind = Enum.SpanKind.SPAN_KIND_UNSPECIFIED
        start_time = '2017-06-25'
        end_time = '2017-06-26'
        labels = {
            '/http/status_code': '200',
            '/component': 'HTTP load balancer',
        }

        child_span = mock.Mock(spec=TraceSpan)
        child_span.name = child_span_name
        child_span.kind = kind
        child_span.parent_span_id = root_span_id
        child_span.span_id = child_span_id
        child_span.start_time = start_time
        child_span.end_time = end_time
        child_span.labels = labels
        child_span.children = []
        child_span.__iter__ = mock.Mock(return_value=iter([child_span]))

        root_span = mock.Mock(spec=TraceSpan)
        root_span.name = root_span_name
        root_span.kind = kind
        root_span.parent_span_id = None
        root_span.span_id = root_span_id
        root_span.start_time = start_time
        root_span.end_time = end_time
        root_span.labels = None
        root_span.children = []
        root_span.__iter__ = mock.Mock(
            return_value=iter([root_span, child_span]))

        child_span_json = {
            'name': child_span.name,
            'kind': kind,
            'parentSpanId': root_span_id,
            'spanId': child_span_id,
            'startTime': start_time,
            'endTime': end_time,
            'labels': labels,
        }

        root_span_json = {
            'name': root_span.name,
            'kind': kind,
            'spanId': root_span_id,
            'startTime': start_time,
            'endTime': end_time,
        }

        trace.spans = [root_span]
        traces = {
            'traces': [
                {
                    'projectId': self.project,
                    'traceId': trace_id,
                    'spans': [
                        root_span_json,
                        child_span_json
                    ]
                }
            ]
        }

        trace.send()

        reporter.report.assert_called_with(traces)

        self.assertEqual(trace.project_id, self.project)
        self.assertEqual(trace.trace_id, trace_id)
        self.assertEqual(trace.spans, [root_span])
