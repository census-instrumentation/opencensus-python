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

from opencensus.trace.tracers import context_tracer
from opencensus.trace import span
from opencensus.trace import execution_context


class TestContextTracer(unittest.TestCase):
    def tearDown(self):
        execution_context.clear()

    def test_constructor_defaults(self):
        from opencensus.trace import print_exporter
        from opencensus.trace import span_context

        tracer = context_tracer.ContextTracer()

        assert isinstance(tracer.span_context, span_context.SpanContext)
        assert isinstance(tracer.exporter, print_exporter.PrintExporter)
        self.assertEqual(tracer._spans_list, [])
        self.assertEqual(tracer.root_span_id, tracer.span_context.span_id)

    def test_constructor_explicit(self):
        from opencensus.trace import span_context

        span_context = span_context.SpanContext()
        exporter = mock.Mock()
        tracer = context_tracer.ContextTracer(
            exporter=exporter, span_context=span_context)

        self.assertIs(tracer.span_context, span_context)
        self.assertIs(tracer.exporter, exporter)
        self.assertEqual(tracer.trace_id, span_context.trace_id)
        self.assertEqual(tracer._spans_list, [])
        self.assertEqual(tracer.root_span_id, span_context.span_id)

    def test_finish_without_spans(self):
        trace_id = '6e0c63257de34c92bf9efcd03927272e'
        tracer = context_tracer.ContextTracer()
        tracer.trace_id = trace_id

        trace = tracer.finish()

        self.assertIsNone(trace)
        self.assertEqual(tracer._spans_list, [])

    def test_finish_with_spans(self):
        tracer = context_tracer.ContextTracer()
        tracer.start_span('span')
        tracer.finish()

        self.assertEqual(tracer._spans_list, [])

    def test_finish_with_tracer_subspans(self):
        tracer = context_tracer.ContextTracer()
        parent = tracer.start_span('parent')
        child = tracer.start_span('child')
        self.assertEqual(child.parent_span, parent)
        tracer.exporter = mock.Mock()
        tracer.finish()

        self.assertEqual(tracer.exporter.export.call_count, 2)
        [[[[c_sd]], _], [[[p_sd]], _]] = tracer.exporter.export.call_args_list

        self.assertEqual(p_sd.span_id, parent.span_id)
        self.assertIsNone(parent.parent_span.span_id)
        self.assertIsNone(p_sd.parent_span_id)
        self.assertEqual(c_sd.span_id, child.span_id)
        self.assertEqual(c_sd.parent_span_id, parent.span_id)

        self.assertEqual(tracer._spans_list, [])

    def test_finish_with_span_subspans(self):
        tracer = context_tracer.ContextTracer()
        parent = tracer.start_span('parent')
        child = parent.span('child')
        self.assertEqual(child.parent_span, parent)
        tracer.exporter = mock.Mock()
        tracer.finish()

        self.assertEqual(tracer.exporter.export.call_count, 1)
        [[[[c_sd, p_sd]], _]] = tracer.exporter.export.call_args_list

        self.assertEqual(p_sd.span_id, parent.span_id)
        self.assertIsNone(parent.parent_span.span_id)
        self.assertIsNone(p_sd.parent_span_id)
        self.assertEqual(c_sd.span_id, child.span_id)
        self.assertEqual(c_sd.parent_span_id, parent.span_id)

        self.assertEqual(tracer._spans_list, [])

    def test_end_leftover_spans(self):
        tracer = context_tracer.ContextTracer()
        tracer._spans_list = [span.Span(name='span')]
        tracer.finish()

        self.assertEqual(tracer._spans_list, [])

    @mock.patch.object(context_tracer.ContextTracer, 'current_span')
    def test_start_span(self, current_span_mock):
        from opencensus.trace import span_context

        span_id = '6e0c63257de34c92'
        span_name = 'test_span'
        mock_span = mock.Mock()
        mock_span.span_id = span_id
        span_context = span_context.SpanContext(span_id=span_id)
        tracer = context_tracer.ContextTracer(span_context=span_context)
        current_span_mock.return_value = mock_span

        span = tracer.start_span(name=span_name)

        self.assertEqual(span.parent_span.span_id, span_id)
        self.assertEqual(span.name, span_name)
        self.assertEqual(len(tracer._spans_list), 1)
        self.assertEqual(span_context.span_id, span.span_id)

    @mock.patch.object(context_tracer.ContextTracer, 'current_span')
    def test_span(self, current_span_mock):
        from opencensus.trace import span_context

        span_id = '6e0c63257de34c92'
        span_name = 'test_span'
        mock_span = mock.Mock()
        mock_span.span_id = span_id
        span_context = span_context.SpanContext(span_id=span_id)
        tracer = context_tracer.ContextTracer(span_context=span_context)
        current_span_mock.return_value = mock_span

        span = tracer.span(name=span_name)

        self.assertEqual(span.parent_span.span_id, span_id)
        self.assertEqual(span.name, span_name)
        self.assertEqual(len(tracer._spans_list), 1)
        self.assertEqual(span_context.span_id, span.span_id)

    @mock.patch.object(context_tracer.ContextTracer, 'current_span')
    def test_end_span_no_active_span(self, mock_current_span):
        tracer = context_tracer.ContextTracer()
        mock_current_span.return_value = None
        self.assertIsNone(tracer.current_span())

        tracer.end_span()

        self.assertIsNone(tracer.current_span())

    @mock.patch.object(context_tracer.ContextTracer, 'current_span')
    def test_end_span_active(self, mock_current_span):
        exporter = mock.Mock()
        tracer = context_tracer.ContextTracer(exporter=exporter)
        mock_span = mock.Mock()
        mock_span.name = 'span'
        mock_span.children = []
        mock_span.status = None
        mock_span.links = None
        mock_span.stack_trace = None
        mock_span.time_events = None
        mock_span.attributes = {}
        mock_span.__iter__ = mock.Mock(return_value=iter([mock_span]))
        parent_span_id = '6e0c63257de34c92'
        mock_span.parent_span.span_id = parent_span_id
        mock_current_span.return_value = mock_span
        tracer.end_span()

        self.assertTrue(mock_span.finish.called)
        self.assertEqual(tracer.span_context.span_id, parent_span_id)
        self.assertFalse(tracer.exporter.export.called)

    @mock.patch.object(context_tracer.ContextTracer, 'current_span')
    def test_end_span_without_parent(self, mock_current_span):
        from opencensus.trace.execution_context import get_current_span

        tracer = context_tracer.ContextTracer()
        mock_span = mock.Mock()
        mock_span.name = 'span'
        mock_span.children = []
        mock_span.status = None
        mock_span.links = None
        mock_span.stack_trace = None
        mock_span.time_events = None
        mock_span.attributes = {}
        mock_span.__iter__ = mock.Mock(return_value=iter([mock_span]))
        mock_current_span.return_value = mock_span
        tracer.end_span()

        cur_span = get_current_span()
        self.assertIsNone(cur_span)

    def test_end_span_batch_export(self):
        exporter = mock.Mock()
        tracer = context_tracer.ContextTracer(exporter=exporter)
        span = tracer.start_span('test')
        parent_span_id = '6e0c63257de34c92'
        span.parent_span.span_id = parent_span_id
        span.finish = mock.Mock()
        tracer.end_span()

        self.assertTrue(span.finish.called)
        self.assertEqual(tracer.span_context.span_id, parent_span_id)
        self.assertTrue(tracer.exporter.export.called)

    def test_list_collected_spans(self):
        tracer = context_tracer.ContextTracer()
        span1 = mock.Mock()
        span2 = mock.Mock()
        tracer._spans_list.append(span1)
        tracer._spans_list.append(span2)

        spans = tracer.list_collected_spans()

        self.assertEqual(spans, [span1, span2])

    def test_add_attribute_to_current_span(self):
        from opencensus.trace.span import Span
        from opencensus.trace import execution_context

        tracer = context_tracer.ContextTracer()
        span1 = mock.Mock(spec=Span)

        span1.attributes = {}
        execution_context.set_current_span(span1)

        attribute_key = 'key'
        attribute_value = 'value'

        tracer.add_attribute_to_current_span(attribute_key, attribute_value)

        span1.add_attribute.assert_called_once_with(attribute_key,
                                                    attribute_value)
