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


class TestFlaskTracer(unittest.TestCase):

    @mock.patch('opencensus.trace.tracer.flask_tracer.get_flask_header')
    @mock.patch('opencensus.trace.propagation.google_cloud_format.from_header')
    def test_constructor_default(
            self, mock_from_header, mock_get_flask_header):
        from opencensus.trace import span_context
        from opencensus.trace.reporters import print_reporter
        from opencensus.trace.samplers import always_on
        from opencensus.trace.tracer import flask_tracer

        trace_id = '6e0c63257de34c92bf9efcd03927272e'
        test_span_context = span_context.SpanContext(trace_id=trace_id)

        mock_from_header.return_value = test_span_context
        mock_get_flask_header.return_value = 'test_flask_header'

        tracer = flask_tracer.FlaskTracer()

        assert isinstance(tracer.reporter, print_reporter.PrintReporter)
        assert isinstance(tracer.sampler, always_on.AlwaysOnSampler)
        assert isinstance(tracer.span_context, span_context.SpanContext)
        self.assertEqual(tracer.span_context, test_span_context)

    def test_constructor_explicit(self):
        from opencensus.trace import span_context
        from opencensus.trace.reporters import print_reporter
        from opencensus.trace.samplers import always_on
        from opencensus.trace.tracer import flask_tracer

        trace_id = '6e0c63257de34c92bf9efcd03927272e'
        span_context = span_context.SpanContext(trace_id=trace_id)
        sampler = always_on.AlwaysOnSampler()
        reporter = print_reporter.PrintReporter()

        tracer = flask_tracer.FlaskTracer(
            span_context=span_context,
            sampler=sampler,
            reporter=reporter)

        self.assertEqual(tracer.span_context, span_context)
        self.assertEqual(tracer.sampler, sampler)
        self.assertEqual(tracer.reporter, reporter)


class Test_get_flask_header(unittest.TestCase):

    @staticmethod
    def _call_fut():
        from opencensus.trace.tracer import flask_tracer

        return flask_tracer.get_flask_header()

    @staticmethod
    def create_app():
        import flask

        app = flask.Flask(__name__)

        @app.route('/')
        def index():
            return 'test flask trace'  # pragma: NO COVER

        return app

    def test_no_request(self):
        trace_header = self._call_fut()
        self.assertIsNone(trace_header)

    def test_no_context_header(self):
        app = self.create_app()
        with app.test_request_context(
                path='/',
                headers={}):
            trace_header = self._call_fut()

        self.assertIsNone(trace_header)

    def test_valid_context_header(self):
        flask_trace_header = 'X_CLOUD_TRACE_CONTEXT'
        expected_trace_id = 'testtraceidflask'
        flask_trace_id = expected_trace_id + '/testspanid'

        app = self.create_app()
        context = app.test_request_context(
            path='/',
            headers={flask_trace_header: flask_trace_id})

        with context:
            trace_header = self._call_fut()

        self.assertEqual(trace_header, flask_trace_id)
