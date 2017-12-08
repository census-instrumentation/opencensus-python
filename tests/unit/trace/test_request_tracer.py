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

from opencensus.trace import request_tracer


class TestRequestTracer(unittest.TestCase):

    def test_constructor_default(self):
        from opencensus.trace.propagation import google_cloud_format
        from opencensus.trace.exporters import print_exporter
        from opencensus.trace.samplers.always_on import AlwaysOnSampler
        from opencensus.trace.span_context import SpanContext
        from opencensus.trace.tracer import context_tracer

        tracer = request_tracer.RequestTracer()

        assert isinstance(tracer.span_context, SpanContext)
        assert isinstance(tracer.sampler, AlwaysOnSampler)
        assert isinstance(tracer.exporter, print_exporter.PrintExporter)
        assert isinstance(
            tracer.propagator,
            google_cloud_format.GoogleCloudFormatPropagator)
        assert isinstance(tracer.tracer, context_tracer.ContextTracer)

    def test_constructor_explicit(self):
        from opencensus.trace.tracer import noop_tracer

        sampler = mock.Mock()
        sampler.should_sample.return_value = False

        exporter = mock.Mock()
        propagator = mock.Mock()
        span_context = mock.Mock()

        tracer = request_tracer.RequestTracer(
            span_context=span_context,
            sampler=sampler,
            exporter=exporter,
            propagator=propagator)

        self.assertIs(tracer.span_context, span_context)
        self.assertIs(tracer.sampler, sampler)
        self.assertIs(tracer.exporter, exporter)
        self.assertIs(tracer.propagator, propagator)
        assert isinstance(tracer.tracer, noop_tracer.NoopTracer)

    def test_should_sample_force_not_trace(self):
        from opencensus.trace import span_context

        span_context = mock.Mock()
        span_context.trace_options.enabled = False
        tracer = request_tracer.RequestTracer(
            span_context=span_context)
        sampled = tracer.should_sample()

        self.assertFalse(sampled)

    def test_should_sample_sampled(self):
        sampler =mock.Mock()
        sampler.should_sample.return_value = True
        tracer = request_tracer.RequestTracer(sampler=sampler)
        sampled = tracer.should_sample()

        self.assertTrue(sampled)

    def test_should_sample_not_sampled(self):
        sampler = mock.Mock()
        sampler.should_sample.return_value = False
        tracer = request_tracer.RequestTracer(sampler=sampler)
        sampled = tracer.should_sample()

        self.assertFalse(sampled)

    def get_tracer_noop_tracer(self):
        from opencensus.trace.tracer import noop_tracer

        sampler = mock.Mock()
        sampler.should_sample.return_value = False
        tracer = request_tracer.RequestTracer(sampler=sampler)

        result = tracer.get_tracer()

        assert isinstance(result, noop_tracer.NoopTracer)

    def get_tracer_context_tracer(self):
        from opencensus.trace.tracer import context_tracer

        sampler = mock.Mock()
        sampler.should_sample.return_value = True
        tracer = request_tracer.RequestTracer(sampler=sampler)

        result = tracer.get_tracer()

        assert isinstance(result, context_tracer.ContextTracer)

    def test_finish_not_sampled(self):
        from opencensus.trace.tracer import noop_tracer

        sampler = mock.Mock()
        sampler.should_sample.return_value = False
        tracer = request_tracer.RequestTracer(sampler=sampler)
        assert isinstance(tracer.tracer, noop_tracer.NoopTracer)
        mock_tracer = mock.Mock()
        tracer.tracer = mock_tracer
        tracer.finish()
        self.assertTrue(mock_tracer.finish.called)

    def test_finish_sampled(self):
        from opencensus.trace.tracer import context_tracer

        sampler = mock.Mock()
        sampler.should_sample.return_value = True
        tracer = request_tracer.RequestTracer(sampler=sampler)
        assert isinstance(tracer.tracer, context_tracer.ContextTracer)
        mock_tracer = mock.Mock()
        tracer.tracer = mock_tracer
        tracer.finish()
        self.assertTrue(mock_tracer.finish.called)

    def test_span_not_sampled(self):
        from opencensus.trace.tracer import base

        sampler = mock.Mock()
        sampler.should_sample.return_value = False
        tracer = request_tracer.RequestTracer(sampler=sampler)

        span = tracer.span()
        assert isinstance(span, base.NullContextManager)

    def test_span_sampled(self):
        sampler = mock.Mock()
        sampler.should_sample.return_value = True
        tracer = request_tracer.RequestTracer(sampler=sampler)
        tracer_mock = mock.Mock()
        tracer.tracer = tracer_mock

        tracer.span()

        self.assertTrue(tracer_mock.span.called)

    def test_start_span_not_sampled(self):
        from opencensus.trace.tracer import base

        sampler = mock.Mock()
        sampler.should_sample.return_value = False
        tracer = request_tracer.RequestTracer(sampler=sampler)

        span = tracer.start_span()

        assert isinstance(span, base.NullContextManager)

    def test_start_span_sampled(self):
        from opencensus.trace import span as trace_span

        sampler = mock.Mock()
        sampler.should_sample.return_value = True
        tracer = request_tracer.RequestTracer(sampler=sampler)
        span = tracer.start_span()

        assert isinstance(span, trace_span.Span)

    def test_end_span_not_sampled(self):
        sampler = mock.Mock()
        sampler.should_sample.return_value = False
        span_context = mock.Mock()
        tracer = request_tracer.RequestTracer(
            sampler=sampler,
            span_context=span_context)

        tracer.end_span()

        self.assertFalse(span_context.span_id.called)

    def test_end_span_sampled(self):
        from opencensus.trace import execution_context

        sampler = mock.Mock()
        sampler.should_sample.return_value = True
        tracer = request_tracer.RequestTracer(sampler=sampler)
        span = mock.Mock()
        span._child_spans = []
        span.attributes = {}
        span.time_events = []
        span.links = []
        span.__iter__ = mock.Mock(
            return_value=iter([span]))
        execution_context.set_current_span(span)

        patch = mock.patch(
            'opencensus.trace.span._get_truncatable_str', mock.Mock())

        with patch:
            tracer.end_span()

        self.assertTrue(span.finish.called)

    def test_current_span_not_sampled(self):
        from opencensus.trace.tracer import base

        sampler = mock.Mock()
        sampler.should_sample.return_value = False
        tracer = request_tracer.RequestTracer(sampler=sampler)

        span = tracer.current_span()

        assert isinstance(span, base.NullContextManager)

    def test_current_span_sampled(self):
        from opencensus.trace import execution_context

        sampler = mock.Mock()
        sampler.should_sample.return_value = True
        tracer = request_tracer.RequestTracer(sampler=sampler)
        span = mock.Mock()
        execution_context.set_current_span(span)

        result = tracer.current_span()

        self.assertEqual(result, span)

    def test_add_attribute_to_current_span_not_sampled(self):
        from opencensus.trace.tracer import base

        sampler = mock.Mock()
        sampler.should_sample.return_value = False
        tracer = request_tracer.RequestTracer(sampler=sampler)
        tracer.add_attribute_to_current_span('key', 'value')

        span = tracer.current_span()

        assert isinstance(span, base.NullContextManager)

    def test_trace_decorator(self):
        tracer = request_tracer.RequestTracer()

        return_value = "test"

        @tracer.trace_decorator()
        def test_decorator():
            return return_value

        returned = test_decorator()

        self.assertEqual(len(tracer.tracer._spans_list), 1)
        self.assertEqual(tracer.tracer._spans_list[0].name, 'test_decorator')
        self.assertEqual(returned, return_value)
