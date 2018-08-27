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

from opencensus.trace.propagation import trace_context_http_header_format


class TestTraceContextPropagator(unittest.TestCase):

    def test_from_header_no_header(self):
        from opencensus.trace.span_context import SpanContext

        propagator = trace_context_http_header_format.\
            TraceContextPropagator()
        span_context = propagator.from_header(None)

        self.assertTrue(isinstance(span_context, SpanContext))

    def test_from_headers_none(self):
        from opencensus.trace.span_context import SpanContext

        propagator = trace_context_http_header_format.\
            TraceContextPropagator()
        span_context = propagator.from_headers(None)

        self.assertTrue(isinstance(span_context, SpanContext))

    def test_from_headers_empty(self):
        from opencensus.trace.span_context import SpanContext

        propagator = trace_context_http_header_format.\
            TraceContextPropagator()
        span_context = propagator.from_headers({})

        self.assertTrue(isinstance(span_context, SpanContext))

    def test_from_headers_with_tracestate(self):
        from opencensus.trace.span_context import SpanContext

        propagator = trace_context_http_header_format.\
            TraceContextPropagator()
        span_context = propagator.from_headers({
            'traceparent': '00-a66ee7820d074463aff4c617a63e929f-91e072af6a404137-01',
            'tracestate': 'foo=1,bar=2,baz=3',
        })

        self.assertTrue(isinstance(span_context, SpanContext))
        self.assertTrue(span_context.tracestate)

    def test_header_type_error(self):
        header = 1234

        propagator = trace_context_http_header_format.\
            TraceContextPropagator()

        with self.assertRaises(TypeError):
            propagator.from_header(header)

    def test_header_version_not_support(self):
        from opencensus.trace.span_context import SpanContext

        header = '01-6e0c63257de34c92bf9efcd03927272e-00f067aa0ba902b7-00'
        propagator = trace_context_http_header_format. \
            TraceContextPropagator()
        span_context = propagator.from_header(header)

        self.assertTrue(isinstance(span_context, SpanContext))

    def test_header_match(self):
        # Trace option is not enabled.
        header = '00-6e0c63257de34c92bf9efcd03927272e-00f067aa0ba902b7-00'
        expected_trace_id = '6e0c63257de34c92bf9efcd03927272e'
        expected_span_id = '00f067aa0ba902b7'

        propagator = trace_context_http_header_format.\
            TraceContextPropagator()
        span_context = propagator.from_header(header)

        self.assertEqual(span_context.trace_id, expected_trace_id)
        self.assertEqual(span_context.span_id, expected_span_id)
        self.assertFalse(span_context.trace_options.enabled)

        # Trace option is enabled.
        header = '00-6e0c63257de34c92bf9efcd03927272e-00f067aa0ba902b7-01'
        expected_trace_id = '6e0c63257de34c92bf9efcd03927272e'
        expected_span_id = '00f067aa0ba902b7'

        propagator = trace_context_http_header_format.\
            TraceContextPropagator()
        span_context = propagator.from_header(header)

        self.assertEqual(span_context.trace_id, expected_trace_id)
        self.assertEqual(span_context.span_id, expected_span_id)
        self.assertTrue(span_context.trace_options.enabled)

    def test_header_match_no_option(self):
        header = '00-6e0c63257de34c92bf9efcd03927272e-00f067aa0ba902b7'
        expected_trace_id = '6e0c63257de34c92bf9efcd03927272e'
        expected_span_id = '00f067aa0ba902b7'

        propagator = trace_context_http_header_format.\
            TraceContextPropagator()
        span_context = propagator.from_header(header)

        self.assertEqual(span_context.trace_id, expected_trace_id)
        self.assertEqual(span_context.span_id, expected_span_id)
        self.assertTrue(span_context.trace_options.enabled)

    def test_header_not_match(self):
        header = '00-invalid_trace_id-66666-00'
        trace_id = 'invalid_trace_id'

        propagator = trace_context_http_header_format.\
            TraceContextPropagator()
        span_context = propagator.from_header(header)

        self.assertNotEqual(span_context.trace_id, trace_id)

    def test_headers_match(self):
        # Trace option is enabled.
        headers = {
            'traceparent':
                '00-6e0c63257de34c92bf9efcd03927272e-00f067aa0ba902b7-01',
        }
        expected_trace_id = '6e0c63257de34c92bf9efcd03927272e'
        expected_span_id = '00f067aa0ba902b7'

        propagator = trace_context_http_header_format.\
            TraceContextPropagator()
        span_context = propagator.from_headers(headers)

        self.assertEqual(span_context.trace_id, expected_trace_id)
        self.assertEqual(span_context.span_id, expected_span_id)
        self.assertTrue(span_context.trace_options.enabled)

    def test_to_header(self):
        from opencensus.trace import span_context
        from opencensus.trace import trace_options

        trace_id = '6e0c63257de34c92bf9efcd03927272e'
        span_id_hex = '00f067aa0ba902b7'
        span_context = span_context.SpanContext(
            trace_id=trace_id,
            span_id=span_id_hex,
            trace_options=trace_options.TraceOptions('1'))

        propagator = trace_context_http_header_format.\
            TraceContextPropagator()

        header = propagator.to_header(span_context)
        expected_header = '00-{}-{}-01'.format(
            trace_id,
            span_id_hex)

        self.assertEqual(header, expected_header)

    def test_to_headers_without_tracestate(self):
        from opencensus.trace import span_context
        from opencensus.trace import trace_options

        trace_id = '6e0c63257de34c92bf9efcd03927272e'
        span_id_hex = '00f067aa0ba902b7'
        span_context = span_context.SpanContext(
            trace_id=trace_id,
            span_id=span_id_hex,
            trace_options=trace_options.TraceOptions('1'))

        propagator = trace_context_http_header_format.\
            TraceContextPropagator()

        headers = propagator.to_headers(span_context)

        self.assertTrue('traceparent' in headers)
        self.assertEqual(headers['traceparent'],
            '00-{}-{}-01'.format(trace_id, span_id_hex))

        self.assertFalse('tracestate' in headers)

    def test_to_headers_with_empty_tracestate(self):
        from opencensus.trace import span_context
        from opencensus.trace import trace_options
        from opencensus.trace.tracestate import Tracestate

        trace_id = '6e0c63257de34c92bf9efcd03927272e'
        span_id_hex = '00f067aa0ba902b7'
        span_context = span_context.SpanContext(
            trace_id=trace_id,
            span_id=span_id_hex,
            tracestate=Tracestate(),
            trace_options=trace_options.TraceOptions('1'))

        propagator = trace_context_http_header_format.\
            TraceContextPropagator()

        headers = propagator.to_headers(span_context)

        self.assertTrue('traceparent' in headers)
        self.assertEqual(headers['traceparent'],
            '00-{}-{}-01'.format(trace_id, span_id_hex))

        self.assertFalse('tracestate' in headers)

    def test_to_headers_with_tracestate(self):
        from opencensus.trace import span_context
        from opencensus.trace import trace_options
        from opencensus.trace.tracestate import Tracestate

        trace_id = '6e0c63257de34c92bf9efcd03927272e'
        span_id_hex = '00f067aa0ba902b7'
        span_context = span_context.SpanContext(
            trace_id=trace_id,
            span_id=span_id_hex,
            tracestate=Tracestate(foo = "xyz"),
            trace_options=trace_options.TraceOptions('1'))

        propagator = trace_context_http_header_format.\
            TraceContextPropagator()

        headers = propagator.to_headers(span_context)

        self.assertTrue('traceparent' in headers)
        self.assertEqual(headers['traceparent'],
            '00-{}-{}-01'.format(trace_id, span_id_hex))

        self.assertTrue('tracestate' in headers)
        self.assertEqual(headers['tracestate'], 'foo=xyz')
