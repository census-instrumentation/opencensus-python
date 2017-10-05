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

from opencensus.trace.propagation import google_cloud_format


class TestGoogleCloudFormatPropagator(unittest.TestCase):

    def test_from_header_no_header(self):
        from opencensus.trace.span_context import SpanContext

        propagator = google_cloud_format.GoogleCloudFormatPropagator()
        span_context = propagator.from_header(None)

        assert isinstance(span_context, SpanContext)

    def test_header_type_error(self):
        header = 1234

        propagator = google_cloud_format.GoogleCloudFormatPropagator()

        with self.assertRaises(TypeError):
            propagator.from_header(header)

    def test_header_match(self):
        # Trace option is not enabled.
        header = '6e0c63257de34c92bf9efcd03927272e/1234;o=0'
        expected_trace_id = '6e0c63257de34c92bf9efcd03927272e'
        expected_span_id = 1234

        propagator = google_cloud_format.GoogleCloudFormatPropagator()
        span_context = propagator.from_header(header)

        self.assertEqual(span_context.trace_id, expected_trace_id)
        self.assertEqual(span_context.span_id, expected_span_id)
        self.assertFalse(span_context.enabled)

        # Trace option is enabled.
        header = '6e0c63257de34c92bf9efcd03927272e/1234;o=1'
        expected_trace_id = '6e0c63257de34c92bf9efcd03927272e'
        expected_span_id = 1234

        propagator = google_cloud_format.GoogleCloudFormatPropagator()
        span_context = propagator.from_header(header)

        self.assertEqual(span_context.trace_id, expected_trace_id)
        self.assertEqual(span_context.span_id, expected_span_id)
        self.assertTrue(span_context.enabled)

    def test_header_match_no_option(self):
        header = '6e0c63257de34c92bf9efcd03927272e/1234'
        expected_trace_id = '6e0c63257de34c92bf9efcd03927272e'
        expected_span_id = 1234

        propagator = google_cloud_format.GoogleCloudFormatPropagator()
        span_context = propagator.from_header(header)

        self.assertEqual(span_context.trace_id, expected_trace_id)
        self.assertEqual(span_context.span_id, expected_span_id)
        self.assertTrue(span_context.enabled)

    def test_header_not_match(self):
        header = 'invalid_trace_id/66666;o=1'
        trace_id = 'invalid_trace_id'

        propagator = google_cloud_format.GoogleCloudFormatPropagator()
        span_context = propagator.from_header(header)

        self.assertNotEqual(span_context.trace_id, trace_id)

    def test_to_header(self):
        from opencensus.trace import span_context

        trace_id = '6e0c63257de34c92bf9efcd03927272e'
        span_id = 1234
        span_context = span_context.SpanContext(
            trace_id=trace_id,
            span_id=span_id,
            enabled=True)

        propagator = google_cloud_format.GoogleCloudFormatPropagator()

        header = propagator.to_header(span_context)
        expected_header = '{}/{};o={}'.format(
            trace_id, span_id, 1)

        self.assertEqual(header, expected_header)
