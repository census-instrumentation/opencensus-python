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

from opencensus.trace.propagation import zipkin_b3_format


class TestZipkinB3FormatPropagator(unittest.TestCase):

    def test_from_carrier_keys_exist(self):
        test_trace_id = '6e0c63257de34c92bf9efcd03927272e'
        test_span_id = '00f067aa0ba902b7'
        test_options = 1

        carrier = {
            zipkin_b3_format._TRACE_ID_KEY: test_trace_id,
            zipkin_b3_format._SPAN_ID_KEY: test_span_id,
            zipkin_b3_format._TRACE_OPTIONS_KEY: test_options,
        }

        propagator = zipkin_b3_format.ZipkinB3FormatPropagator()

        span_context = propagator.from_carrier(carrier)

        self.assertEqual(span_context.trace_id, test_trace_id)
        self.assertEqual(span_context.span_id, test_span_id)
        self.assertEqual(span_context.trace_options.enabled, bool(test_options))

    def test_from_carrier_keys_not_exist(self):
        carrier = {}

        propagator = zipkin_b3_format.ZipkinB3FormatPropagator()
        span_context = propagator.from_carrier(carrier)

        self.assertIsNotNone(span_context.trace_id)
        # Span_id should be None here which indicates no parent span_id for
        # the child spans
        self.assertIsNone(span_context.span_id)
        self.assertTrue(span_context.trace_options.enabled)

    def test_to_carrier_has_span_id(self):
        test_trace_id = '6e0c63257de34c92bf9efcd03927272e'
        test_span_id = '00f067aa0ba902b7'
        test_options = '2'

        span_context = mock.Mock()
        span_context.trace_id = test_trace_id
        span_context.span_id = test_span_id
        span_context.trace_options.trace_options_byte = test_options

        carrier = {}
        propagator = zipkin_b3_format.ZipkinB3FormatPropagator()
        carrier = propagator.to_carrier(span_context, carrier)

        self.assertEqual(
            carrier[zipkin_b3_format._TRACE_ID_KEY],
            test_trace_id)
        self.assertEqual(
            carrier[zipkin_b3_format._SPAN_ID_KEY],
            str(test_span_id))
        self.assertEqual(
            carrier[zipkin_b3_format._TRACE_OPTIONS_KEY],
            test_options)

    def test_to_carrier_no_span_id(self):
        test_trace_id = '6e0c63257de34c92bf9efcd03927272e'
        test_options = '1'

        span_context = mock.Mock()
        span_context.trace_id = test_trace_id
        span_context.span_id = None
        span_context.trace_options.trace_options_byte = test_options

        carrier = {}
        propagator = zipkin_b3_format.ZipkinB3FormatPropagator()
        carrier = propagator.to_carrier(span_context, carrier)

        self.assertEqual(
            carrier[zipkin_b3_format._TRACE_ID_KEY],
            test_trace_id)
        self.assertIsNone(
            carrier.get(zipkin_b3_format._SPAN_ID_KEY))
        self.assertEqual(
            carrier[zipkin_b3_format._TRACE_OPTIONS_KEY],
            test_options)
