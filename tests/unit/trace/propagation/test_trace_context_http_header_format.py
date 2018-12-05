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
            'traceparent':
            '00-12345678901234567890123456789012-1234567890123456-00',
            'tracestate':
            'foo=1,bar=2,baz=3',
        })

        self.assertTrue(isinstance(span_context, SpanContext))
        self.assertTrue(span_context.tracestate)

    def test_from_headers_tracestate_limit(self):
        propagator = trace_context_http_header_format.\
            TraceContextPropagator()

        span_context = propagator.from_headers({
            'traceparent':
            '00-12345678901234567890123456789012-1234567890123456-00',
            'tracestate':
            ','.join([
                'a00=0,a01=1,a02=2,a03=3,a04=4,a05=5,a06=6,a07=7,a08=8,a09=9',
                'b00=0,b01=1,b02=2,b03=3,b04=4,b05=5,b06=6,b07=7,b08=8,b09=9',
                'c00=0,c01=1,c02=2,c03=3,c04=4,c05=5,c06=6,c07=7,c08=8,c09=9',
                'd00=0,d01=1,d02=2',
            ]),
        })

        self.assertFalse(span_context.tracestate)

    def test_from_headers_tracestate_duplicated_keys(self):
        propagator = trace_context_http_header_format.\
            TraceContextPropagator()

        span_context = propagator.from_headers({
            'traceparent':
            '00-12345678901234567890123456789012-1234567890123456-00',
            'tracestate':
            'foo=1,bar=2,foo=3',
        })

        self.assertFalse(span_context.tracestate)

    def test_header_all_zero(self):
        propagator = trace_context_http_header_format. \
            TraceContextPropagator()

        trace_id = '00000000000000000000000000000000'
        span_context = propagator.from_headers({
            'traceparent':
            '00-00000000000000000000000000000000-1234567890123456-00',
        })

        self.assertNotEqual(span_context.trace_id, trace_id)

        span_id = '0000000000000000'
        span_context = propagator.from_headers({
            'traceparent':
            '00-12345678901234567890123456789012-0000000000000000-00',
        })

        self.assertNotEqual(span_context.span_id, span_id)

    def test_header_version_not_supported(self):
        propagator = trace_context_http_header_format. \
            TraceContextPropagator()

        trace_id = '12345678901234567890123456789012'
        span_context = propagator.from_headers({
            'traceparent':
            'ff-12345678901234567890123456789012-1234567890123456-00',
        })

        self.assertNotEqual(span_context.trace_id, trace_id)

        span_context = propagator.from_headers({
            'traceparent':
            '00-12345678901234567890123456789012-1234567890123456-00-residue',
        })

        self.assertNotEqual(span_context.trace_id, trace_id)

    def test_header_match(self):
        propagator = trace_context_http_header_format.\
            TraceContextPropagator()

        trace_id = '12345678901234567890123456789012'
        span_id = '1234567890123456'

        # Trace option is not enabled.
        span_context = propagator.from_headers({
            'traceparent':
            '00-12345678901234567890123456789012-1234567890123456-00',
        })

        self.assertEqual(span_context.trace_id, trace_id)
        self.assertEqual(span_context.span_id, span_id)
        self.assertFalse(span_context.trace_options.enabled)

        # Trace option is enabled.
        span_context = propagator.from_headers({
            'traceparent':
            '00-12345678901234567890123456789012-1234567890123456-01',
        })

        self.assertEqual(span_context.trace_id, trace_id)
        self.assertEqual(span_context.span_id, span_id)
        self.assertTrue(span_context.trace_options.enabled)

    def test_header_not_match(self):
        propagator = trace_context_http_header_format.\
            TraceContextPropagator()

        trace_id = 'invalid_trace_id'
        span_context = propagator.from_headers({
            'traceparent':
            '00-invalid_trace_id-66666-00',
        })

        self.assertNotEqual(span_context.trace_id, trace_id)

    def test_to_headers_without_tracestate(self):
        from opencensus.trace import span_context
        from opencensus.trace import trace_options

        propagator = trace_context_http_header_format.\
            TraceContextPropagator()

        trace_id = '12345678901234567890123456789012'
        span_id_hex = '1234567890123456'
        span_context = span_context.SpanContext(
            trace_id=trace_id,
            span_id=span_id_hex,
            trace_options=trace_options.TraceOptions('1'))

        headers = propagator.to_headers(span_context)

        self.assertTrue('traceparent' in headers)
        self.assertEqual(headers['traceparent'], '00-{}-{}-01'.format(
            trace_id, span_id_hex))

        self.assertFalse('tracestate' in headers)

    def test_to_headers_with_empty_tracestate(self):
        from opencensus.trace import span_context
        from opencensus.trace import trace_options
        from opencensus.trace.tracestate import Tracestate

        propagator = trace_context_http_header_format.\
            TraceContextPropagator()

        trace_id = '12345678901234567890123456789012'
        span_id_hex = '1234567890123456'
        span_context = span_context.SpanContext(
            trace_id=trace_id,
            span_id=span_id_hex,
            tracestate=Tracestate(),
            trace_options=trace_options.TraceOptions('1'))

        headers = propagator.to_headers(span_context)

        self.assertTrue('traceparent' in headers)
        self.assertEqual(headers['traceparent'], '00-{}-{}-01'.format(
            trace_id, span_id_hex))

        self.assertFalse('tracestate' in headers)

    def test_to_headers_with_tracestate(self):
        from opencensus.trace import span_context
        from opencensus.trace import trace_options
        from opencensus.trace.tracestate import Tracestate

        propagator = trace_context_http_header_format.\
            TraceContextPropagator()

        trace_id = '12345678901234567890123456789012'
        span_id_hex = '1234567890123456'
        span_context = span_context.SpanContext(
            trace_id=trace_id,
            span_id=span_id_hex,
            tracestate=Tracestate(foo="xyz"),
            trace_options=trace_options.TraceOptions('1'))

        headers = propagator.to_headers(span_context)

        self.assertTrue('traceparent' in headers)
        self.assertEqual(headers['traceparent'], '00-{}-{}-01'.format(
            trace_id, span_id_hex))

        self.assertTrue('tracestate' in headers)
        self.assertEqual(headers['tracestate'], 'foo=xyz')
