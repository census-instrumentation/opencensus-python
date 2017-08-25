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

import json
import unittest

import mock
import six

try:
    from webapp2 import RequestHandler
except SyntaxError:
    # webapp2 is not supported in Python3, so we just skip the unit test in
    # that case.
    RequestHandler = object


@unittest.skipIf(six.PY3, 'webapp2 is Python 2 only')
class TestWebApp2Tracer(unittest.TestCase):

    @mock.patch('opencensus.trace.tracer.webapp2_tracer.get_webapp2_header')
    def test_constructor_default(
            self, mock_get_webapp2_header):
        from opencensus.trace import span_context
        from opencensus.trace.reporters import print_reporter
        from opencensus.trace.samplers import always_on
        from opencensus.trace.propagation import google_cloud_format
        from opencensus.trace.tracer import webapp2_tracer

        trace_id = '6e0c63257de34c92bf9efcd03927272e'
        test_span_context = span_context.SpanContext(trace_id=trace_id)

        patch = mock.patch.object(
            google_cloud_format.GoogleCloudFormatPropagator,
            'from_header',
            return_value=test_span_context)
        mock_get_webapp2_header.return_value = 'test_webapp2_header'

        with patch:
            tracer = webapp2_tracer.WebApp2Tracer()

        assert isinstance(tracer.reporter, print_reporter.PrintReporter)
        assert isinstance(tracer.sampler, always_on.AlwaysOnSampler)
        assert isinstance(
            tracer.propagator,
            google_cloud_format.GoogleCloudFormatPropagator)
        assert isinstance(tracer.span_context, span_context.SpanContext)
        self.assertEqual(tracer.span_context, test_span_context)

    def test_constructor_explicit(self):
        from opencensus.trace import span_context
        from opencensus.trace.reporters import print_reporter
        from opencensus.trace.samplers import always_on
        from opencensus.trace.propagation import google_cloud_format
        from opencensus.trace.tracer import webapp2_tracer

        trace_id = '6e0c63257de34c92bf9efcd03927272e'
        span_context = span_context.SpanContext(trace_id=trace_id)
        sampler = always_on.AlwaysOnSampler()
        reporter = print_reporter.PrintReporter()
        propagator = google_cloud_format.GoogleCloudFormatPropagator()

        tracer = webapp2_tracer.WebApp2Tracer(
            span_context=span_context,
            sampler=sampler,
            reporter=reporter,
            propagator=propagator)

        self.assertEqual(tracer.span_context, span_context)
        self.assertEqual(tracer.sampler, sampler)
        self.assertEqual(tracer.reporter, reporter)
        self.assertEqual(tracer.propagator, propagator)


class _GetTraceHeader(RequestHandler):
    def get(self):
        from opencensus.trace.tracer import webapp2_tracer

        header = webapp2_tracer.get_webapp2_header()
        self.response.content_type = 'application/json'
        self.response.out.write(json.dumps(header))


@unittest.skipIf(six.PY3, 'webapp2 is Python 2 only')
class Test_get_webapp2_header(unittest.TestCase):

    @staticmethod
    def create_app():
        import webapp2

        app = webapp2.WSGIApplication(
            [('/', _GetTraceHeader),]
        )

        return app

    def test_not_in_request_context(self):
        from opencensus.trace.tracer import webapp2_tracer

        header = webapp2_tracer.get_webapp2_header()

        self.assertIsNone(header)

    def test_no_context_header(self):
        import webob

        req = webob.BaseRequest.blank('/')
        response = req.get_response(self.create_app())
        trace_id = json.loads(response.body)

        self.assertEqual(None, trace_id)

    def test_valid_context_header(self):
        import webob

        webapp2_trace_header = 'X-Cloud-Trace-Context'
        trace_id = 'testtraceidwebapp2'
        webapp2_trace_id = trace_id + '/testspanid'

        req = webob.BaseRequest.blank(
            '/',
            headers={webapp2_trace_header: webapp2_trace_id})
        response = req.get_response(self.create_app())
        trace_header = json.loads(response.body)

        self.assertEqual(trace_header, webapp2_trace_id)
