#!/usr/bin/env python
# -*- coding: utf-8 -*-

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

from opencensus.trace.ext.flask import flask_middleware


class TestFlaskMiddleware(unittest.TestCase):

    @staticmethod
    def create_app():
        import flask

        app = flask.Flask(__name__)

        @app.route('/')
        def index():
            return 'test flask trace'  # pragma: NO COVER

        return app

    def tearDown(self):
        from opencensus.trace import execution_context

        execution_context.clear()

    def test_constructor_default(self):
        from opencensus.trace.reporters import print_reporter
        from opencensus.trace.samplers import always_on
        from opencensus.trace.propagation import google_cloud_format

        app = mock.Mock()
        middleware = flask_middleware.FlaskMiddleware(app=app)

        self.assertIs(app, middleware.app)
        self.assertTrue(app.before_request.called)
        self.assertTrue(app.after_request.called)
        assert isinstance(middleware.sampler, always_on.AlwaysOnSampler)
        assert isinstance(middleware.reporter, print_reporter.PrintReporter)
        assert isinstance(
            middleware.propagator,
            google_cloud_format.GoogleCloudFormatPropagator)

    def test_constructor_explicit(self):
        app = mock.Mock()
        sampler = mock.Mock()
        reporter = mock.Mock()
        propagator = mock.Mock()

        middleware = flask_middleware.FlaskMiddleware(
            app=app,
            sampler=sampler,
            reporter=reporter,
            propagator=propagator)

        self.assertIs(middleware.app, app)
        self.assertIs(middleware.sampler, sampler)
        self.assertIs(middleware.reporter, reporter)
        self.assertIs(middleware.propagator, propagator)
        self.assertTrue(app.before_request.called)
        self.assertTrue(app.after_request.called)

    def test__before_request(self):
        from opencensus.trace import execution_context

        flask_trace_header = 'X_CLOUD_TRACE_CONTEXT'
        trace_id = '2dd43a1d6b2549c6bc2a1a54c2fc0b05'
        span_id = 1234
        flask_trace_id = '{}/{}'.format(trace_id, span_id)

        app = self.create_app()
        flask_middleware.FlaskMiddleware(app=app)
        context = app.test_request_context(
            path='/',
            headers={flask_trace_header: flask_trace_id})

        with context:
            app.preprocess_request()
            tracer = execution_context.get_opencensus_tracer()
            self.assertIsNotNone(tracer)

            span = tracer.current_span()

            expected_labels = {
                '/http/url': u'http://localhost/',
                '/http/method': 'GET',
            }

            self.assertEqual(span.labels, expected_labels)
            self.assertEqual(span.parent_span_id, span_id)

            span_context = tracer.span_context
            self.assertEqual(span_context.trace_id, trace_id)

    def test_header_encoding(self):
        # The test is for detecting the encoding compatibility issue in
        # Python2 and Python3 and what flask does for encoding the headers.
        # This test case is expected to fail at the check_trace_id method
        # in SpanContext because it cannot match the pattern for trace_id,
        # And a new trace_id will generate for the context.
        from opencensus.trace import execution_context

        flask_trace_header = 'X_CLOUD_TRACE_CONTEXT'
        trace_id = "你好"
        span_id = 1234
        flask_trace_id = '{}/{}'.format(trace_id, span_id)

        app = self.create_app()
        flask_middleware.FlaskMiddleware(app=app)
        context = app.test_request_context(
            path='/',
            headers={flask_trace_header: flask_trace_id})

        with context:
            app.preprocess_request()
            tracer = execution_context.get_opencensus_tracer()
            self.assertIsNotNone(tracer)

            span = tracer.current_span()

            expected_labels = {
                '/http/url': u'http://localhost/',
                '/http/method': 'GET',
            }

            self.assertEqual(span.labels, expected_labels)
            self.assertIsNone(span.parent_span_id)

            span_context = tracer.span_context
            self.assertNotEqual(span_context.trace_id, trace_id)

    def test_header_is_none(self):
        from opencensus.trace import execution_context

        app = self.create_app()
        flask_middleware.FlaskMiddleware(app=app)
        context = app.test_request_context(
            path='/')

        with context:
            app.preprocess_request()
            tracer = execution_context.get_opencensus_tracer()
            self.assertIsNotNone(tracer)

            span = tracer.current_span()

            expected_labels = {
                '/http/url': u'http://localhost/',
                '/http/method': 'GET',
            }

            self.assertEqual(span.labels, expected_labels)
            self.assertIsNone(span.parent_span_id)

    def test__after_request_not_sampled(self):
        from opencensus.trace.samplers import always_off

        flask_trace_header = 'X_CLOUD_TRACE_CONTEXT'
        trace_id = '2dd43a1d6b2549c6bc2a1a54c2fc0b05'
        span_id = 1234
        flask_trace_id = '{}/{}'.format(trace_id, span_id)
        sampler = always_off.AlwaysOffSampler()

        app = self.create_app()
        flask_middleware.FlaskMiddleware(app=app, sampler=sampler)

        response = app.test_client().get(
            '/',
            headers={flask_trace_header: flask_trace_id})

        self.assertEqual(response.status_code, 200)

    def test__after_request_sampled(self):
        flask_trace_header = 'X_CLOUD_TRACE_CONTEXT'
        trace_id = '2dd43a1d6b2549c6bc2a1a54c2fc0b05'
        span_id = 1234
        flask_trace_id = '{}/{}'.format(trace_id, span_id)

        app = self.create_app()
        flask_middleware.FlaskMiddleware(app=app)

        response = app.test_client().get(
            '/',
            headers={flask_trace_header: flask_trace_id})

        self.assertEqual(response.status_code, 200)
