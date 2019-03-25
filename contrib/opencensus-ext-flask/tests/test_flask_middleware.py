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

from google.rpc import code_pb2
import flask
import mock

from opencensus.ext.flask import flask_middleware
from opencensus.ext.jaeger import trace_exporter as jaeger_exporter
from opencensus.ext.ocagent import trace_exporter as ocagent_exporter
from opencensus.ext.stackdriver import trace_exporter as stackdriver_exporter
from opencensus.ext.zipkin import trace_exporter as zipkin_exporter
from opencensus.trace import execution_context
from opencensus.trace import print_exporter
from opencensus.trace import span as span_module
from opencensus.trace import span_data
from opencensus.trace import stack_trace
from opencensus.trace import status
from opencensus.trace.blank_span import BlankSpan
from opencensus.trace.propagation import google_cloud_format
from opencensus.trace.samplers import always_off, always_on, ProbabilitySampler
from opencensus.trace.span_context import SpanContext
from opencensus.trace.trace_options import TraceOptions
from opencensus.trace.tracers import base
from opencensus.trace.tracers import noop_tracer


class FlaskTestException(Exception):
    pass


class TestFlaskMiddleware(unittest.TestCase):

    @staticmethod
    def create_app():
        app = flask.Flask(__name__)

        @app.route('/')
        def index():
            return 'test flask trace'  # pragma: NO COVER

        @app.route('/_ah/health')
        def health_check():
            return 'test health check'  # pragma: NO COVER

        @app.route('/error')
        def error():
            raise FlaskTestException('error')

        return app

    def tearDown(self):
        from opencensus.trace import execution_context

        execution_context.clear()

    def test_constructor_default(self):
        app = mock.Mock(config={})
        middleware = flask_middleware.FlaskMiddleware(app=app)

        self.assertIs(app, middleware.app)
        self.assertTrue(app.before_request.called)
        self.assertTrue(app.after_request.called)
        assert isinstance(middleware.sampler, always_on.AlwaysOnSampler)
        assert isinstance(middleware.exporter, print_exporter.PrintExporter)
        assert isinstance(
            middleware.propagator,
            google_cloud_format.GoogleCloudFormatPropagator)

    def test_constructor_explicit(self):
        app = mock.Mock(config={})
        sampler = mock.Mock()
        exporter = mock.Mock()
        propagator = mock.Mock()

        middleware = flask_middleware.FlaskMiddleware(
            app=app,
            sampler=sampler,
            exporter=exporter,
            propagator=propagator)

        self.assertIs(middleware.app, app)
        self.assertIs(middleware.sampler, sampler)
        self.assertIs(middleware.exporter, exporter)
        self.assertIs(middleware.propagator, propagator)
        self.assertTrue(app.before_request.called)
        self.assertTrue(app.after_request.called)

    def test_init_app(self):
        app = mock.Mock()

        middleware = flask_middleware.FlaskMiddleware()
        middleware.init_app(app)

        self.assertIs(middleware.app, app)
        self.assertTrue(app.before_request.called)
        self.assertTrue(app.after_request.called)

    def test_init_app_config_stackdriver_exporter(self):
        app = mock.Mock()
        app.config = {
            'OPENCENSUS_TRACE': {
                'SAMPLER': ProbabilitySampler,
                'EXPORTER': stackdriver_exporter.StackdriverExporter,
                'PROPAGATOR': google_cloud_format.GoogleCloudFormatPropagator,
            },
            'OPENCENSUS_TRACE_PARAMS': {
                'BLACKLIST_PATHS': ['/_ah/health'],
                'GCP_EXPORTER_PROJECT': None,
                'SAMPLING_RATE': 0.5,
                'ZIPKIN_EXPORTER_SERVICE_NAME': 'my_service',
                'ZIPKIN_EXPORTER_HOST_NAME': 'localhost',
                'ZIPKIN_EXPORTER_PORT': 9411,
                'ZIPKIN_EXPORTER_PROTOCOL': 'http',
            },
        }

        class StackdriverExporter(object):
            def __init__(self, *args, **kwargs):
                pass

        middleware = flask_middleware.FlaskMiddleware(
            exporter=StackdriverExporter
        )
        middleware.init_app(app)

        self.assertIs(middleware.app, app)
        self.assertTrue(app.before_request.called)
        self.assertTrue(app.after_request.called)

    def test_init_app_config_zipkin_exporter(self):

        service_name = 'foo'
        host_name = 'localhost'
        port = 1234
        app = mock.Mock()
        app.config = {
            'OPENCENSUS_TRACE': {
                'SAMPLER': ProbabilitySampler,
                'EXPORTER': zipkin_exporter.ZipkinExporter,
                'PROPAGATOR': google_cloud_format.GoogleCloudFormatPropagator,
            },
            'OPENCENSUS_TRACE_PARAMS': {
                'ZIPKIN_EXPORTER_SERVICE_NAME': service_name,
                'ZIPKIN_EXPORTER_HOST_NAME': host_name,
                'ZIPKIN_EXPORTER_PORT': port,
                'ZIPKIN_EXPORTER_PROTOCOL': 'http',
            },
        }

        middleware = flask_middleware.FlaskMiddleware()
        middleware.init_app(app)

        self.assertIs(middleware.app, app)
        self.assertTrue(app.before_request.called)
        self.assertTrue(app.after_request.called)

        assert isinstance(
            middleware.exporter, zipkin_exporter.ZipkinExporter)
        self.assertEqual(middleware.exporter.service_name, service_name)
        self.assertEqual(middleware.exporter.host_name, host_name)
        self.assertEqual(middleware.exporter.port, port)

    def test_init_app_config_zipkin_exporter_service_name_param(self):

        service_name = 'foo'
        host_name = 'localhost'
        port = 1234
        app = mock.Mock()
        app.config = {
            'OPENCENSUS_TRACE': {
                'SAMPLER': ProbabilitySampler,
                'EXPORTER': zipkin_exporter.ZipkinExporter,
                'PROPAGATOR': google_cloud_format.GoogleCloudFormatPropagator,
            },
            'OPENCENSUS_TRACE_PARAMS': {
                'SERVICE_NAME': service_name,
                'ZIPKIN_EXPORTER_HOST_NAME': host_name,
                'ZIPKIN_EXPORTER_PORT': port,
                'ZIPKIN_EXPORTER_PROTOCOL': 'http',
            },
        }

        middleware = flask_middleware.FlaskMiddleware()
        middleware.init_app(app)

        self.assertIs(middleware.app, app)
        self.assertTrue(app.before_request.called)
        self.assertTrue(app.after_request.called)

        assert isinstance(
            middleware.exporter, zipkin_exporter.ZipkinExporter)
        self.assertEqual(middleware.exporter.service_name, service_name)
        self.assertEqual(middleware.exporter.host_name, host_name)
        self.assertEqual(middleware.exporter.port, port)

    def test_init_app_config_jaeger_exporter(self):
        service_name = 'foo'
        app = mock.Mock()
        app.config = {
            'OPENCENSUS_TRACE': {
                'SAMPLER': ProbabilitySampler,
                'EXPORTER': jaeger_exporter.JaegerExporter,
                'PROPAGATOR': google_cloud_format.GoogleCloudFormatPropagator,
            },
            'OPENCENSUS_TRACE_PARAMS': {
                'SERVICE_NAME': service_name,
            },
        }

        middleware = flask_middleware.FlaskMiddleware()
        middleware.init_app(app)

        self.assertIs(middleware.app, app)
        self.assertTrue(app.before_request.called)
        self.assertTrue(app.after_request.called)

        assert isinstance(
            middleware.exporter, jaeger_exporter.JaegerExporter)
        self.assertEqual(middleware.exporter.service_name, service_name)

    def test_init_app_config_ocagent_trace_exporter(self):
        app = mock.Mock()
        app.config = {
            'OPENCENSUS_TRACE': {
                'SAMPLER': ProbabilitySampler,
                'EXPORTER': ocagent_exporter.TraceExporter,
                'PROPAGATOR': google_cloud_format.GoogleCloudFormatPropagator,
            },
            'OPENCENSUS_TRACE_PARAMS': {
                'SERVICE_NAME': 'foo',
                'OCAGENT_TRACE_EXPORTER_ENDPOINT': 'localhost:50001'
            }
        }

        middleware = flask_middleware.FlaskMiddleware()
        middleware.init_app(app)

        self.assertIs(middleware.app, app)
        assert isinstance(
            middleware.exporter, ocagent_exporter.TraceExporter)
        self.assertEqual(middleware.exporter.service_name, 'foo')
        self.assertEqual(middleware.exporter.endpoint, 'localhost:50001')

        self.assertTrue(app.before_request.called)
        self.assertTrue(app.after_request.called)

    def test_init_app_config_ocagent_trace_exporter_default_endpoint(self):
        app = mock.Mock()
        app.config = {
            'OPENCENSUS_TRACE': {
                'SAMPLER': ProbabilitySampler,
                'EXPORTER': ocagent_exporter.TraceExporter,
                'PROPAGATOR': google_cloud_format.GoogleCloudFormatPropagator,
            },
            'OPENCENSUS_TRACE_PARAMS': {
                'SERVICE_NAME': 'foo'
            }
        }

        middleware = flask_middleware.FlaskMiddleware()
        middleware.init_app(app)

        self.assertIs(middleware.app, app)
        assert isinstance(
            middleware.exporter, ocagent_exporter.TraceExporter)
        self.assertEqual(middleware.exporter.service_name, 'foo')
        self.assertEqual(middleware.exporter.endpoint,
                         ocagent_exporter.DEFAULT_ENDPOINT)

        self.assertTrue(app.before_request.called)
        self.assertTrue(app.after_request.called)

    def test__before_request(self):
        from opencensus.trace import execution_context

        flask_trace_header = 'X-Cloud-Trace-Context'
        trace_id = '2dd43a1d6b2549c6bc2a1a54c2fc0b05'
        span_id = '6e0c63257de34c92'
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

            expected_attributes = {
                'http.url': u'http://localhost/',
                'http.method': 'GET',
            }

            self.assertEqual(span.span_kind, span_module.SpanKind.SERVER)
            self.assertEqual(span.attributes, expected_attributes)
            self.assertEqual(span.parent_span.span_id, span_id)

            span_context = tracer.span_context
            self.assertEqual(span_context.trace_id, trace_id)

    def test__before_request_blacklist(self):
        flask_trace_header = 'X-Cloud-Trace-Context'
        trace_id = '2dd43a1d6b2549c6bc2a1a54c2fc0b05'
        span_id = '6e0c63257de34c92'
        flask_trace_id = '{}/{}'.format(trace_id, span_id)

        app = self.create_app()
        flask_middleware.FlaskMiddleware(app=app)
        context = app.test_request_context(
            path='/_ah/health',
            headers={flask_trace_header: flask_trace_id})

        with context:
            app.preprocess_request()
            tracer = execution_context.get_opencensus_tracer()
            assert isinstance(tracer, noop_tracer.NoopTracer)

            span = tracer.current_span()

            assert isinstance(span, BlankSpan)

    def test_header_encoding(self):
        # The test is for detecting the encoding compatibility issue in
        # Python2 and Python3 and what flask does for encoding the headers.
        # This test case is expected to fail at the check_trace_id method
        # in SpanContext because it cannot match the pattern for trace_id,
        # And a new trace_id will generate for the context.

        flask_trace_header = 'X-Cloud-Trace-Context'
        trace_id = "你好"
        span_id = '6e0c63257de34c92'
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

            expected_attributes = {
                'http.url': u'http://localhost/',
                'http.method': 'GET',
            }

            self.assertEqual(span.attributes, expected_attributes)
            assert isinstance(span.parent_span, base.NullContextManager)

            span_context = tracer.span_context
            self.assertNotEqual(span_context.trace_id, trace_id)

    def test_header_is_none(self):
        app = self.create_app()
        flask_middleware.FlaskMiddleware(app=app)
        context = app.test_request_context(
            path='/')

        with context:
            app.preprocess_request()
            tracer = execution_context.get_opencensus_tracer()
            self.assertIsNotNone(tracer)

            span = tracer.current_span()

            expected_attributes = {
                'http.url': u'http://localhost/',
                'http.method': 'GET',
            }

            self.assertEqual(span.attributes, expected_attributes)
            assert isinstance(span.parent_span, base.NullContextManager)

    def test__after_request_not_sampled(self):
        flask_trace_header = 'X-Cloud-Trace-Context'
        trace_id = '2dd43a1d6b2549c6bc2a1a54c2fc0b05'
        span_id = '6e0c63257de34c92'
        flask_trace_id = '{}/{}'.format(trace_id, span_id)
        sampler = always_off.AlwaysOffSampler()

        app = self.create_app()
        flask_middleware.FlaskMiddleware(app=app, sampler=sampler)

        response = app.test_client().get(
            '/',
            headers={flask_trace_header: flask_trace_id})

        self.assertEqual(response.status_code, 200)

    def test__after_request_sampled(self):
        flask_trace_header = 'X-Cloud-Trace-Context'
        trace_id = '2dd43a1d6b2549c6bc2a1a54c2fc0b05'
        span_id = '6e0c63257de34c92'
        flask_trace_id = '{}/{}'.format(trace_id, span_id)

        app = self.create_app()
        flask_middleware.FlaskMiddleware(app=app)

        response = app.test_client().get(
            '/',
            headers={flask_trace_header: flask_trace_id})

        self.assertEqual(response.status_code, 200)

    def test__after_request_blacklist(self):
        flask_trace_header = 'X-Cloud-Trace-Context'
        trace_id = '2dd43a1d6b2549c6bc2a1a54c2fc0b05'
        span_id = '6e0c63257de34c92'
        flask_trace_id = '{}/{}'.format(trace_id, span_id)

        app = self.create_app()
        flask_middleware.FlaskMiddleware(app=app)

        response = app.test_client().get(
            '/_ah/health',
            headers={flask_trace_header: flask_trace_id})

        tracer = execution_context.get_opencensus_tracer()

        self.assertEqual(response.status_code, 200)
        assert isinstance(tracer, noop_tracer.NoopTracer)

    def test_teardown_include_exception(self):
        mock_exporter = mock.MagicMock()
        app = self.create_app()
        flask_middleware.FlaskMiddleware(app=app, exporter=mock_exporter)
        response = app.test_client().get('/error')

        self.assertEqual(response.status_code, 500)

        exported_spandata = mock_exporter.export.call_args[0][0][0]
        self.assertIsInstance(exported_spandata, span_data.SpanData)
        self.assertIsInstance(exported_spandata.status, status.Status)
        self.assertEqual(exported_spandata.status.code, code_pb2.UNKNOWN)
        self.assertEqual(exported_spandata.status.message, 'error')

    def test_teardown_include_exception_and_traceback(self):
        mock_exporter = mock.MagicMock()
        app = self.create_app()
        app.config['TESTING'] = True
        flask_middleware.FlaskMiddleware(app=app, exporter=mock_exporter)
        with self.assertRaises(FlaskTestException):
            app.test_client().get('/error')

        exported_spandata = mock_exporter.export.call_args[0][0][0]
        self.assertIsInstance(exported_spandata, span_data.SpanData)
        self.assertIsInstance(exported_spandata.status, status.Status)
        self.assertEqual(exported_spandata.status.code, code_pb2.UNKNOWN)
        self.assertEqual(exported_spandata.status.message, 'error')
        self.assertIsInstance(
            exported_spandata.stack_trace, stack_trace.StackTrace
        )
        self.assertIsNotNone(exported_spandata.stack_trace.stack_trace_hash_id)
        self.assertNotEqual(exported_spandata.stack_trace.stack_frames, [])

    def test_teardown_include_exception_and_traceback_span_disabled(self):
        sampler = always_off.AlwaysOffSampler()
        app = self.create_app()
        app.config['TESTING'] = True
        middleware = flask_middleware.FlaskMiddleware(app=app, sampler=sampler)

        # TODO: send trace options in header (#465)
        original_method = middleware.propagator.from_headers

        def nope(*args, **kwargs):
            trace_options = TraceOptions()
            trace_options.set_enabled(False)
            return SpanContext(trace_options=trace_options)

        middleware.propagator.from_headers = nope

        with self.assertRaises(FlaskTestException):
            app.test_client().get('/error')

        middleware.propagator.from_headers = original_method
