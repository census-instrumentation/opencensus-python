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

from opencensus.trace.tracer import context_tracer


class TestContextTracer(unittest.TestCase):

    def test_constructor_defaults(self):
        from opencensus.trace import span_context
        from opencensus.trace import trace
        from opencensus.trace.reporters import print_reporter
        from opencensus.trace.samplers import always_on

        tracer = context_tracer.ContextTracer()

        assert isinstance(tracer.reporter, print_reporter.PrintReporter)
        assert isinstance(tracer.span_context, span_context.SpanContext)
        assert isinstance(tracer.sampler, always_on.AlwaysOnSampler)
        assert isinstance(tracer.cur_trace, trace.Trace)
        self.assertTrue(tracer.enabled)
        self.assertEqual(tracer._span_stack, [])
        self.assertEqual(tracer.root_span_id, tracer.span_context.span_id)

    def test_constructor_explicit(self):
        from opencensus.trace import span_context
        from opencensus.trace.reporters import print_reporter
        from opencensus.trace.samplers import fixed_rate

        reporter = print_reporter.PrintReporter()
        span_context = span_context.SpanContext()
        sampler = fixed_rate.FixedRateSampler(rate=0)
        tracer = context_tracer.ContextTracer(
            reporter=reporter,
            span_context=span_context,
            sampler=sampler)

        self.assertIs(tracer.reporter, reporter)
        self.assertIs(tracer.span_context, span_context)
        self.assertIs(tracer.sampler, sampler)
        self.assertEqual(tracer.trace_id, span_context.trace_id)
        self.assertFalse(tracer.enabled)
        self.assertEqual(tracer._span_stack, [])
        self.assertEqual(tracer.root_span_id, span_context.span_id)
        assert isinstance(tracer.cur_trace, context_tracer.NullObject)

    def test_set_enabled_force_not_trace(self):
        from opencensus.trace import span_context

        span_context = span_context.SpanContext(enabled=False)
        tracer = context_tracer.ContextTracer(
            span_context=span_context)
        enabled = tracer.set_enabled()

        self.assertFalse(enabled)

    def test_set_enabled_should_sample(self):
        from opencensus.trace.samplers import always_on

        sampler = always_on.AlwaysOnSampler()
        tracer = context_tracer.ContextTracer(sampler=sampler)
        enabled = tracer.set_enabled()

        self.assertTrue(enabled)

    def test_set_enabled_should_not_sample(self):
        from opencensus.trace.samplers import always_off

        sampler = always_off.AlwaysOffSampler()
        tracer = context_tracer.ContextTracer(sampler=sampler)
        enabled = tracer.set_enabled()

        self.assertFalse(enabled)

    def test_trace_decorator(self):
        tracer = context_tracer.ContextTracer()

        return_value = "test"

        @tracer.trace_decorator()
        def test_decorator():
            return return_value

        returned = test_decorator()

        self.assertEqual(len(tracer.cur_trace.spans), 1)
        self.assertEqual(tracer.cur_trace.spans[0].name, 'test_decorator')
        self.assertEqual(returned, return_value)

    def test_trace_not_enabled(self):
        tracer = context_tracer.ContextTracer()
        tracer.enabled = False
        cur_trace = tracer.trace()

        assert isinstance(cur_trace, context_tracer.NullObject)

    def test_trace_enabled(self):
        from opencensus.trace import trace

        tracer = context_tracer.ContextTracer()
        cur_trace = tracer.trace()

        self.assertEqual(cur_trace.trace_id, tracer.trace_id)
        assert isinstance(cur_trace, trace.Trace)

    def test_start_trace_not_enabled(self):
        tracer = context_tracer.ContextTracer()
        cur_trace = mock.Mock()
        tracer.enabled = False
        tracer.cur_trace = cur_trace

        tracer.start_trace()
        self.assertFalse(cur_trace.start.called)

    def test_start_trace_enabled(self):
        tracer = context_tracer.ContextTracer()
        cur_trace = mock.Mock()
        tracer.cur_trace = cur_trace

        tracer.start_trace()
        self.assertTrue(cur_trace.start.called)

    def test_end_trace_not_enabled(self):
        tracer = context_tracer.ContextTracer()
        cur_trace = mock.Mock()
        tracer.enabled = False
        tracer.cur_trace = cur_trace

        tracer.end_trace()
        self.assertFalse(cur_trace.finish.called)

    def test_end_trace_enabled(self):
        tracer = context_tracer.ContextTracer()
        cur_trace = mock.Mock()
        tracer.cur_trace = cur_trace

        tracer.end_trace()
        self.assertTrue(cur_trace.finish.called)

    def test_span_not_enabled(self):
        tracer = context_tracer.ContextTracer()
        tracer.enabled = False

        span = tracer.span()
        assert isinstance(span, context_tracer.NullObject)

    def test_span_enabled(self):
        from opencensus.trace import span_context

        span_id = 1234
        span_name = 'test_span'
        span_context = span_context.SpanContext(span_id=span_id)
        tracer = context_tracer.ContextTracer(span_context=span_context)

        span = tracer.span(name=span_name)

        self.assertEqual(span.parent_span_id, span_id)
        self.assertEqual(span.name, span_name)
        self.assertEqual(len(tracer.cur_trace.spans), 1)
        self.assertEqual(len(tracer._span_stack), 1)
        self.assertEqual(span_context.span_id, span.span_id)

    def test_start_span_not_enabled(self):
        tracer = context_tracer.ContextTracer()
        tracer.enabled = False

        tracer.start_span()

        self.assertEqual(len(tracer._span_stack), 0)
        self.assertEqual(len(tracer.cur_trace.spans), 0)

    def test_start_span_enabled(self):
        tracer = context_tracer.ContextTracer()
        tracer.start_span()

        self.assertEqual(len(tracer._span_stack), 1)
        self.assertEqual(len(tracer.cur_trace.spans), 1)

    def test_end_span_not_enabled(self):
        tracer = context_tracer.ContextTracer()
        tracer.enabled = False
        span = mock.Mock()
        tracer._span_stack.append(span)
        tracer.end_span()

        self.assertFalse(span.finish.called)

    def test_end_span_enabled_index_error(self):
        tracer = context_tracer.ContextTracer()

        with self.assertRaises(IndexError):
            tracer.end_span()

    def test_end_span_enabled_empty_span_stack(self):
        tracer = context_tracer.ContextTracer()
        span = mock.Mock()
        tracer._span_stack.append(span)
        tracer.end_span()

        self.assertEqual(tracer.span_context.span_id, tracer.root_span_id)
        self.assertTrue(span.finish.called)

    def test_end_span_enabled_span_stack_not_empty(self):
        tracer = context_tracer.ContextTracer()
        span1 = mock.Mock()
        span2 = mock.Mock()
        tracer._span_stack.append(span1)
        tracer._span_stack.append(span2)
        tracer.end_span()

        self.assertEqual(
            tracer.span_context.span_id,
            tracer._span_stack[-1].span_id)
        self.assertEqual(tracer.span_context.span_id, span1.span_id)
        self.assertTrue(span2.finish.called)

    def test_list_collected_spans(self):
        tracer = context_tracer.ContextTracer()
        span1 = mock.Mock()
        span2 = mock.Mock()
        tracer.cur_trace.spans.append(span1)
        tracer.cur_trace.spans.append(span2)

        spans = tracer.list_collected_spans()

        self.assertEqual(spans, [span1, span2])

    def test_add_label_to_spans(self):
        from opencensus.trace.trace_span import TraceSpan

        tracer = context_tracer.ContextTracer()
        cur_trace = mock.Mock()
        span1 = TraceSpan(name='span1')
        span2 = TraceSpan(name='span2')
        cur_trace.spans = [span1, span2]
        tracer.cur_trace = cur_trace

        label_key = 'key'
        label_value = 'value'
        expected_labels = {label_key: label_value}

        tracer.add_label_to_spans(label_key, label_value)

        self.assertEqual(span1.labels, expected_labels)
        self.assertEqual(span2.labels, expected_labels)
