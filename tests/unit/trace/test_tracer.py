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

from opencensus.trace import tracer as tracer_module
from opencensus.trace import span_data


class TestTracer(unittest.TestCase):
    def test_constructor_default(self):
        from opencensus.trace import print_exporter
        from opencensus.trace.propagation import google_cloud_format
        from opencensus.trace.samplers.always_on import AlwaysOnSampler
        from opencensus.trace.span_context import SpanContext
        from opencensus.trace.tracers import context_tracer

        tracer = tracer_module.Tracer()

        assert isinstance(tracer.span_context, SpanContext)
        assert isinstance(tracer.sampler, AlwaysOnSampler)
        assert isinstance(tracer.exporter, print_exporter.PrintExporter)
        assert isinstance(tracer.propagator,
                          google_cloud_format.GoogleCloudFormatPropagator)
        assert isinstance(tracer.tracer, context_tracer.ContextTracer)

    def test_constructor_explicit(self):
        from opencensus.trace.tracers import noop_tracer

        sampler = mock.Mock()
        sampler.should_sample.return_value = False

        exporter = mock.Mock()
        propagator = mock.Mock()
        span_context = mock.Mock()
        span_context.trace_options.enabled = False

        tracer = tracer_module.Tracer(
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

        span_context = mock.Mock()
        span_context.trace_options.enabled = False
        sampler = mock.Mock()
        sampler.should_sample.return_value = False
        tracer = tracer_module.Tracer(
            span_context=span_context, sampler=sampler)
        sampled = tracer.should_sample()

        self.assertFalse(sampled)

    def test_should_sample_sampled(self):
        sampler = mock.Mock()
        sampler.should_sample.return_value = True
        tracer = tracer_module.Tracer(sampler=sampler)
        sampled = tracer.should_sample()

        self.assertTrue(sampled)

    def test_should_sample_not_sampled(self):
        sampler = mock.Mock()
        sampler.should_sample.return_value = False
        span_context = mock.Mock()
        span_context.trace_options.enabled = False
        tracer = tracer_module.Tracer(
            span_context=span_context, sampler=sampler)
        sampled = tracer.should_sample()

        self.assertFalse(sampled)

    def get_tracer_noop_tracer(self):
        from opencensus.trace.tracers import noop_tracer

        sampler = mock.Mock()
        sampler.should_sample.return_value = False
        tracer = tracer_module.Tracer(sampler=sampler)

        result = tracer.get_tracer()

        assert isinstance(result, noop_tracer.NoopTracer)

    def get_tracer_context_tracer(self):
        from opencensus.trace.tracers import context_tracer

        sampler = mock.Mock()
        sampler.should_sample.return_value = True
        tracer = tracer_module.Tracer(sampler=sampler)

        result = tracer.get_tracer()

        assert isinstance(result, context_tracer.ContextTracer)
        self.assertTrue(tracer.span_context.trace_options.enabled)

    def test_finish_not_sampled(self):
        from opencensus.trace.tracers import noop_tracer

        sampler = mock.Mock()
        sampler.should_sample.return_value = False
        span_context = mock.Mock()
        span_context.trace_options.enabled = False
        tracer = tracer_module.Tracer(
            span_context=span_context, sampler=sampler)
        assert isinstance(tracer.tracer, noop_tracer.NoopTracer)
        mock_tracer = mock.Mock()
        tracer.tracer = mock_tracer
        tracer.finish()
        self.assertTrue(mock_tracer.finish.called)

    def test_finish_sampled(self):
        from opencensus.trace.tracers import context_tracer

        sampler = mock.Mock()
        sampler.should_sample.return_value = True
        tracer = tracer_module.Tracer(sampler=sampler)
        assert isinstance(tracer.tracer, context_tracer.ContextTracer)
        mock_tracer = mock.Mock()
        tracer.tracer = mock_tracer
        tracer.finish()
        self.assertTrue(mock_tracer.finish.called)

    def test_span_not_sampled(self):
        from opencensus.trace.blank_span import BlankSpan

        sampler = mock.Mock()
        sampler.should_sample.return_value = False
        span_context = mock.Mock()
        span_context.trace_options.enabled = False
        tracer = tracer_module.Tracer(
            span_context=span_context, sampler=sampler)

        span = tracer.span()

        # Test nested span not sampled
        child_span = span.span()
        tracer.finish()

        assert isinstance(span, BlankSpan)
        assert isinstance(child_span, BlankSpan)

    def test_span_sampled(self):
        sampler = mock.Mock()
        sampler.should_sample.return_value = True
        tracer = tracer_module.Tracer(sampler=sampler)
        tracer_mock = mock.Mock()
        tracer.tracer = tracer_mock

        tracer.span()

        self.assertTrue(tracer_mock.span.called)

    def test_start_span_not_sampled(self):
        from opencensus.trace.blank_span import BlankSpan

        sampler = mock.Mock()
        sampler.should_sample.return_value = False
        span_context = mock.Mock()
        span_context.trace_options.enabled = False
        tracer = tracer_module.Tracer(
            span_context=span_context, sampler=sampler)

        span = tracer.start_span()

        assert isinstance(span, BlankSpan)

    def test_start_span_sampled(self):
        from opencensus.trace import span as trace_span

        sampler = mock.Mock()
        sampler.should_sample.return_value = True
        tracer = tracer_module.Tracer(sampler=sampler)
        span = tracer.start_span()

        assert isinstance(span, trace_span.Span)

    def test_end_span_not_sampled(self):
        sampler = mock.Mock()
        sampler.should_sample.return_value = False
        span_context = mock.Mock()
        span_context.trace_options.enabled = False
        tracer = tracer_module.Tracer(
            sampler=sampler, span_context=span_context)

        tracer.end_span()

        self.assertFalse(span_context.span_id.called)

    def test_end_span_sampled(self):
        from opencensus.trace import execution_context

        sampler = mock.Mock()
        sampler.should_sample.return_value = True
        tracer = tracer_module.Tracer(sampler=sampler)
        span = mock.Mock()
        span.attributes = {}
        span.time_events = []
        span.links = []
        span.children = []
        span.__iter__ = mock.Mock(return_value=iter([span]))
        execution_context.set_current_span(span)

        with mock.patch('opencensus.trace.span.utils.get_truncatable_str'):
            tracer.end_span()

        self.assertTrue(span.finish.called)

    def test_current_span_not_sampled(self):
        from opencensus.trace.blank_span import BlankSpan

        sampler = mock.Mock()
        sampler.should_sample.return_value = False
        span_context = mock.Mock()
        span_context.trace_options.enabled = False
        tracer = tracer_module.Tracer(
            sampler=sampler, span_context=span_context)

        span = tracer.current_span()

        assert isinstance(span, BlankSpan)

    def test_current_span_sampled(self):
        from opencensus.trace import execution_context

        sampler = mock.Mock()
        sampler.should_sample.return_value = True
        tracer = tracer_module.Tracer(sampler=sampler)
        span = mock.Mock()
        execution_context.set_current_span(span)

        result = tracer.current_span()

        self.assertEqual(result, span)

    def test_add_attribute_to_current_span_not_sampled(self):
        from opencensus.trace.blank_span import BlankSpan

        sampler = mock.Mock()
        sampler.should_sample.return_value = False
        span_context = mock.Mock()
        span_context.trace_options.enabled = False
        tracer = tracer_module.Tracer(
            span_context=span_context, sampler=sampler)
        tracer.add_attribute_to_current_span('key', 'value')

        span = tracer.current_span()

        assert isinstance(span, BlankSpan)

    def test_trace_decorator(self):
        mock_exporter = mock.MagicMock()
        tracer = tracer_module.Tracer(exporter=mock_exporter)

        return_value = "test"

        @tracer.trace_decorator()
        def test_decorator():
            return return_value

        returned = test_decorator()

        self.assertEqual(returned, return_value)
        self.assertEqual(mock_exporter.export.call_count, 1)
        exported_spandata = mock_exporter.export.call_args[0][0][0]
        self.assertIsInstance(exported_spandata, span_data.SpanData)
        self.assertEqual(exported_spandata.name, 'test_decorator')
