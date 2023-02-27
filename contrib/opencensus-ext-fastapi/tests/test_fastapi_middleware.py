# Copyright 2022, OpenCensus Authors
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

import sys
import traceback
import unittest
import mock
from unittest.mock import ANY

from fastapi import FastAPI
from starlette.testclient import TestClient

from opencensus.ext.fastapi.fastapi_middleware import FastAPIMiddleware
from opencensus.trace import span as span_module, print_exporter, samplers
from opencensus.trace import tracer as tracer_module
from opencensus.trace.propagation import trace_context_http_header_format


class FastAPITestException(Exception):
    pass


class TestFastAPIMiddleware(unittest.TestCase):

    def tearDown(self) -> None:
        from opencensus.trace import execution_context
        execution_context.clear()

        return super().tearDown()

    def create_app(self):
        app = FastAPI()

        @app.get('/')
        def index():
            return 'test fastapi trace'  # pragma: NO COVER

        @app.get('/wiki/{entry}')
        def wiki(entry):
            return 'test fastapi trace'  # pragma: NO COVER

        @app.get('/health')
        def health_check():
            return 'test health check'  # pragma: NO COVER

        @app.get('/error')
        def error():
            raise FastAPITestException('test error')

        return app

    def test_constructor_default(self):
        app = self.create_app()
        middleware = FastAPIMiddleware(app)

        self.assertIs(middleware.app, app)
        self.assertIsNone(middleware.excludelist_paths)
        self.assertIsNone(middleware.excludelist_hostnames)
        self.assertIsInstance(middleware.sampler, samplers.AlwaysOnSampler)
        self.assertIsInstance(middleware.exporter, print_exporter.PrintExporter)
        self.assertIsInstance(middleware.propagator, trace_context_http_header_format.TraceContextPropagator)

    def test_constructor_explicit(self):
        excludelist_paths = mock.Mock()
        excludelist_hostnames = mock.Mock()
        sampler = mock.Mock()
        exporter = mock.Mock()
        propagator = mock.Mock()

        app = self.create_app()
        middleware = FastAPIMiddleware(
            app=app,
            excludelist_paths=excludelist_paths,
            excludelist_hostnames=excludelist_hostnames,
            sampler=sampler,
            exporter=exporter,
            propagator=propagator)

        self.assertEqual(middleware.app, app)
        self.assertEqual(middleware.excludelist_paths, excludelist_paths)
        self.assertEqual(middleware.excludelist_hostnames, excludelist_hostnames)
        self.assertEqual(middleware.sampler, sampler)
        self.assertEqual(middleware.exporter, exporter)
        self.assertEqual(middleware.propagator, propagator)

    @mock.patch.object(tracer_module.Tracer, "finish")
    @mock.patch.object(tracer_module.Tracer, "end_span")
    @mock.patch.object(tracer_module.Tracer, "start_span")
    def test_request(self, mock_m1, mock_m2, mock_m3):
        app = self.create_app()
        app.add_middleware(FastAPIMiddleware, sampler=samplers.AlwaysOnSampler())

        test_client = TestClient(app)
        test_client.get("/wiki/Rabbit")

        mock_span = mock_m1.return_value
        self.assertEqual(mock_span.add_attribute.call_count, 6)
        mock_span.add_attribute.assert_has_calls([
            mock.call("http.host", "testserver"),
            mock.call("http.method", "GET"),
            mock.call("http.path", "/wiki/Rabbit"),
            mock.call("http.url", "http://testserver/wiki/Rabbit"),
            mock.call("http.route", "/wiki/Rabbit"),
            mock.call("http.status_code", 200)
        ])
        mock_m2.assert_called_once()
        mock_m3.assert_called_once()

        self.assertEqual(
            mock_span.span_kind,
            span_module.SpanKind.SERVER)
        self.assertEqual(
            mock_span.name,
            "[{}]{}".format("GET", "http://testserver/wiki/Rabbit"))

    @mock.patch.object(FastAPIMiddleware, "_prepare_tracer")
    def test_request_excludelist(self, mock_m):
        app = self.create_app()
        app.add_middleware(FastAPIMiddleware, excludelist_paths=["health"], sampler=samplers.AlwaysOnSampler())

        test_client = TestClient(app)
        test_client.get("/health")

        mock_m.assert_not_called()

    @mock.patch.object(tracer_module.Tracer, "finish")
    @mock.patch.object(tracer_module.Tracer, "end_span")
    @mock.patch.object(tracer_module.Tracer, "start_span")
    def test_request_exception(self, mock_m1, mock_m2, mock_m3):
        app = self.create_app()
        app.add_middleware(FastAPIMiddleware)

        test_client = TestClient(app)

        with self.assertRaises(FastAPITestException):
            test_client.get("/error")

        mock_span = mock_m1.return_value
        self.assertEqual(mock_span.add_attribute.call_count, 8)
        mock_span.add_attribute.assert_has_calls([
            mock.call("http.host", "testserver"),
            mock.call("http.method", "GET"),
            mock.call("http.path", "/error"),
            mock.call("http.url", "http://testserver/error"),
            mock.call("http.route", "/error"),
            mock.call("error.name", "FastAPITestException"),
            mock.call("error.message", "test error"),
            mock.call("stacktrace", ANY)
        ])
        mock_m2.assert_called_once()
        mock_m3.assert_called_once()

    def test_request_exception_stacktrace(self):
        tb = None
        try:
            raise RuntimeError("bork bork bork")
        except Exception as exc:
            test_exception = exc
            if hasattr(exc, "__traceback__"):
                tb = exc.__traceback__
            else:
                _, _, tb = sys.exc_info()

        app = self.create_app()
        middleware = FastAPIMiddleware(app)

        mock_span = mock.Mock()
        mock_span.add_attribute = mock.Mock()
        middleware._handle_exception(mock_span, test_exception)

        mock_span.add_attribute.assert_has_calls([
            mock.call("error.name", "RuntimeError"),
            mock.call("error.message", "bork bork bork"),
            mock.call("stacktrace", "\n".join(traceback.format_tb(tb))),
            mock.call("http.status_code", 500)
        ])
