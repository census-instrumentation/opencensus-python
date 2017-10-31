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

from opencensus.trace.tracer import context_tracer


class TestContextTracer(unittest.TestCase):

    def test_constructor_defaults(self):
        from opencensus.trace import span_context

        tracer = context_tracer.ContextTracer()

        assert isinstance(tracer.span_context, span_context.SpanContext)
        self.assertEqual(tracer._spans_list, [])
        self.assertEqual(tracer.root_span_id, tracer.span_context.span_id)

    def test_constructor_explicit(self):
        from opencensus.trace import span_context

        span_context = span_context.SpanContext()
        tracer = context_tracer.ContextTracer(span_context=span_context)

        self.assertIs(tracer.span_context, span_context)
        self.assertEqual(tracer.trace_id, span_context.trace_id)
        self.assertEqual(tracer._spans_list, [])
        self.assertEqual(tracer.root_span_id, span_context.span_id)

    def test_finish_without_spans(self):
        spans = []
        trace_id = '6e0c63257de34c92bf9efcd03927272e'
        tracer = context_tracer.ContextTracer()
        tracer.trace_id = trace_id

        trace = tracer.finish()

        self.assertIsNone(trace)

    def test_finish_with_spans(self):
        from opencensus.trace.enums import Enum
        from opencensus.trace.span import Span

        tracer = context_tracer.ContextTracer()
        trace_id = '6e0c63257de34c92bf9efcd03927272e'
        tracer.trace_id = trace_id
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

        child_span = mock.Mock(spec=Span)
        child_span.name = child_span_name
        child_span.kind = kind
        child_span.span_id = child_span_id
        child_span.start_time = start_time
        child_span.end_time = end_time
        child_span.labels = labels
        child_span.children = []
        child_span.__iter__ = mock.Mock(return_value=iter([child_span]))

        root_span = mock.Mock(spec=Span)
        root_span.name = root_span_name
        root_span.kind = kind
        root_span.parent_span = None
        root_span.span_id = root_span_id
        root_span.start_time = start_time
        root_span.end_time = end_time
        root_span.labels = None
        root_span.children = []
        root_span.__iter__ = mock.Mock(
            return_value=iter([root_span, child_span]))

        child_span.parent_span = root_span

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

        tracer._spans_list = [root_span]

        trace = {
            'traceId': trace_id,
            'spans': [
                root_span_json,
                child_span_json
            ]
        }

        trace_json = tracer.finish()

        self.assertEqual(trace_json, trace)

    @mock.patch.object(context_tracer.ContextTracer, 'current_span')
    def test_span(self, current_span_mock):
        from opencensus.trace import span_context

        span_id = 1234
        parent_span_id = 6666
        span_name = 'test_span'
        mock_span = mock.Mock()
        mock_span.span_id = parent_span_id
        mock_current_span = mock_span
        span_context = span_context.SpanContext(span_id=span_id)
        tracer = context_tracer.ContextTracer(span_context=span_context)
        current_span_mock.return_value = mock_current_span

        span = tracer.span(name=span_name)

        self.assertEqual(span.parent_span.span_id, parent_span_id)
        self.assertEqual(span.name, span_name)
        self.assertEqual(len(tracer._spans_list), 1)
        self.assertEqual(span_context.span_id, span.span_id)

    def test_start_span(self):
        tracer = context_tracer.ContextTracer()
        tracer.start_span()

        self.assertEqual(len(tracer._spans_list), 1)

    @mock.patch.object(context_tracer.ContextTracer, 'current_span')
    def test_end_span_no_active_span(self, mock_current_span):
        tracer = context_tracer.ContextTracer()
        mock_current_span.return_value = None
        self.assertIsNone(tracer.current_span())

        tracer.end_span()

        self.assertIsNone(tracer.current_span())

    @mock.patch.object(context_tracer.ContextTracer, 'current_span')
    def test_end_span_active(self, mock_current_span):
        tracer = context_tracer.ContextTracer()
        mock_span = mock.Mock()
        parent_span_id = 1234
        mock_span.parent_span.span_id = parent_span_id
        mock_current_span.return_value = mock_span
        tracer.end_span()

        self.assertTrue(mock_span.finish.called)
        self.assertEqual(tracer.span_context.span_id, parent_span_id)

    @mock.patch.object(context_tracer.ContextTracer, 'current_span')
    def test_end_span_without_parent(self, mock_current_span):
        from opencensus.trace.execution_context import get_current_span

        tracer = context_tracer.ContextTracer()
        mock_span = mock.Mock()
        mock_current_span.return_value = mock_span
        tracer.end_span()

        cur_span = get_current_span()
        self.assertIsNone(cur_span)

    def test_list_collected_spans(self):
        tracer = context_tracer.ContextTracer()
        span1 = mock.Mock()
        span2 = mock.Mock()
        tracer._spans_list.append(span1)
        tracer._spans_list.append(span2)

        spans = tracer.list_collected_spans()

        self.assertEqual(spans, [span1, span2])

    def test_add_label_to_current_span(self):
        from opencensus.trace.span import Span
        from opencensus.trace import execution_context

        tracer = context_tracer.ContextTracer()
        span1 = mock.Mock(spec=Span)

        span1.labels = {}
        execution_context.set_current_span(span1)

        label_key = 'key'
        label_value = 'value'

        tracer.add_label_to_current_span(label_key, label_value)

        span1.add_label.assert_called_once_with(label_key, label_value)

    def test_add_label_to_spans(self):
        from opencensus.trace.span import Span

        tracer = context_tracer.ContextTracer()
        span1 = mock.Mock(spec=Span)
        span2 = mock.Mock(spec=Span)

        span1.labels = {}
        span2.labels = {}
        tracer._spans_list = [span1, span2]

        label_key = 'key'
        label_value = 'value'

        tracer.add_label_to_spans(label_key, label_value)

        span1.add_label.assert_called_once_with(label_key, label_value)
        span2.add_label.assert_called_once_with(label_key, label_value)
