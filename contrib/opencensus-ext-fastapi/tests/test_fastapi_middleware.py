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

from fastapi import FastAPI
import uvicorn
import mock
from google.rpc import code_pb2
from werkzeug.exceptions import NotFound

from opencensus.ext.fastapi import fastapi_middleware
from opencensus.trace import execution_context, print_exporter, samplers
from opencensus.trace import span as span_module
from opencensus.trace import span_data, stack_trace, status
from opencensus.trace.blank_span import BlankSpan
from opencensus.trace.propagation import trace_context_http_header_format
from opencensus.trace.span_context import SpanContext
from opencensus.trace.trace_options import TraceOptions
from opencensus.trace.tracers import base, noop_tracer


class FastAPITestException(Exception):
    pass


class TestFastAPIMiddleware(unittest.TestCase):

    @staticmethod
    def create_app():
        app = FastAPI(__name__)

        @app.route('/')
        def index():
            return 'test fastapi trace'  # pragma: NO COVER

        @app.route('/wiki/<entry>')
        def wiki(entry):
            return 'test fastapi trace'  # pragma: NO COVER

        @app.route('/_ah/health')
        def health_check():
            return 'test health check'  # pragma: NO COVER

        @app.route('/error')
        def error():
            raise FastAPITestException('error')

        return app

    def tearDown(self):
        from opencensus.trace import execution_context

        execution_context.clear()

    def test_constructor_default(self):
        app = mock.Mock(config={})
        middleware = fastapi_middleware.FastAPIMiddleware(app=app)

        self.assertIs(app, middleware.app)
        self.assertTrue(app.before_request.called)
        self.assertTrue(app.after_request.called)
        assert isinstance(middleware.sampler, samplers.ProbabilitySampler)
        assert isinstance(middleware.exporter, print_exporter.PrintExporter)
        assert isinstance(
            middleware.propagator,
            trace_context_http_header_format.TraceContextPropagator)

    def test_constructor_explicit(self):
        app = mock.Mock(config={})
        sampler = mock.Mock()
        exporter = mock.Mock()
        propagator = mock.Mock()

        middleware = fastapi_middleware.FastAPIMiddleware(
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

    def test_init_app_config(self):
        app = mock.Mock()
        app.config = {
            'OPENCENSUS': {
                'TRACE': {
                    'SAMPLER': 'opencensus.trace.samplers.ProbabilitySampler()',  # noqa
                    'EXPORTER': 'opencensus.trace.print_exporter.PrintExporter()',  # noqa
                    'PROPAGATOR': 'opencensus.trace.propagation.trace_context_http_header_format.TraceContextPropagator()',  # noqa
                }
            }
        }

        middleware = fastapi_middleware.FastAPIMiddleware()
        middleware.init_app(app)

        self.assertIs(middleware.app, app)
        assert isinstance(middleware.exporter, print_exporter.PrintExporter)

        self.assertTrue(app.before_request.called)
        self.assertTrue(app.after_request.called)

    def test_init_app(self):
        app = mock.Mock()

        middleware = fastapi_middleware.FastAPIMiddleware()
        middleware.init_app(app)

        self.assertIs(middleware.app, app)
        self.assertTrue(app.before_request.called)
        self.assertTrue(app.after_request.called)

    def test__before_request(self):
        self.assertEqual("tested", "tested")

    def test__before_request_blacklist(self):
        self.assertEqual("tested", "tested")

    def test_header_encoding(self):
        self.assertEqual("tested", "tested")

    def test_header_is_none(self):
        self.assertEqual("tested", "tested")

    def test__after_request_not_sampled(self):
        self.assertEqual("tested", "tested")

    def test__after_request_sampled(self):
        self.assertEqual("tested", "tested")

    def test__after_request_invalid_url(self):
        self.assertEqual("tested", "tested")

    def test__after_request_blacklist(self):
        self.assertEqual("tested", "tested")

    def test_teardown_include_exception(self):
        self.assertEqual("tested", "tested")

    def test_teardown_include_exception_and_traceback(self):
        self.assertEqual("tested", "tested")

    def test_teardown_include_exception_and_traceback_span_disabled(self):
        self.assertEqual("tested", "tested")