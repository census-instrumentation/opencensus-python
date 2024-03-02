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
import asyncio
from http import HTTPStatus
from unittest import IsolatedAsyncioTestCase

import mock
from aiohttp import ClientPayloadError, InvalidURL

from opencensus.ext.aiohttp import trace
from opencensus.trace import execution_context
from opencensus.trace import status as status_module
from opencensus.trace.span import SpanKind
from opencensus.trace.tracers import noop_tracer


class TestAiohttpTrace(IsolatedAsyncioTestCase):
    def test_trace_integration(self):
        mock_wrap = mock.Mock()
        patch_wrapt = mock.patch("wrapt.wrap_function_wrapper", mock_wrap)

        with patch_wrapt:
            trace.trace_integration()

            self.assertIsInstance(
                execution_context.get_opencensus_tracer(), noop_tracer.NoopTracer
            )
            mock_wrap.assert_called_once_with(
                module="aiohttp",
                name="ClientSession._request",
                wrapper=trace.wrap_session_request,
            )

    def test_trace_integration_set_tracer(self):
        mock_wrap = mock.Mock()
        patch_wrapt = mock.patch("wrapt.wrap_function_wrapper", mock_wrap)

        TmpTracer = noop_tracer.NoopTracer

        with patch_wrapt:
            trace.trace_integration(tracer=TmpTracer())

            self.assertIsInstance(execution_context.get_opencensus_tracer(), TmpTracer)
            mock_wrap.assert_called_once_with(
                module="aiohttp",
                name="ClientSession._request",
                wrapper=trace.wrap_session_request,
            )

    async def test_wrap_session_request(self):
        mock_tracer = MockTracer()
        patch_tracer = mock.patch(
            "opencensus.ext.requests.trace.execution_context." "get_opencensus_tracer",
            return_value=mock_tracer,
        )
        patch_thread = mock.patch(
            "opencensus.ext.requests.trace.execution_context." "is_exporter",
            return_value=False,
        )

        http_host = "localhost:8080"
        http_path = "/test"
        http_url = f"http://{http_host}{http_path}"
        http_method = "POST"
        status = HTTPStatus.OK
        kwargs = {}

        wrapped = mock.AsyncMock(return_value=mock.Mock(status=status))

        with patch_tracer, patch_thread:
            await trace.wrap_session_request(
                wrapped, "ClientSession._request", (http_method, http_url), kwargs
            )

        expected_attributes = {
            "component": "HTTP",
            "http.host": http_host,
            "http.method": http_method,
            "http.path": http_path,
            "http.status_code": status,
            "http.url": http_url,
        }
        expected_name = http_path
        expected_status = status_module.Status(0)

        self.assertEqual(SpanKind.CLIENT, mock_tracer._span.span_kind)
        self.assertEqual(expected_attributes, mock_tracer._span.attributes)
        self.assertEqual(expected_name, mock_tracer._span.name)
        self.assertEqual(expected_status.__dict__, mock_tracer._span.status.__dict__)

    async def test_wrap_session_request_excludelist_ok(self):
        mock_tracer = MockTracer()
        patch_tracer = mock.patch(
            "opencensus.ext.requests.trace.execution_context." "get_opencensus_tracer",
            return_value=mock_tracer,
        )
        patch_attr = mock.patch(
            "opencensus.ext.requests.trace.execution_context." "get_opencensus_attr",
            return_value=None,
        )
        patch_thread = mock.patch(
            "opencensus.ext.requests.trace.execution_context." "is_exporter",
            return_value=False,
        )

        http_host = "localhost:8080"
        http_path = "/test"
        http_url = f"http://{http_host}{http_path}"
        http_method = "POST"
        status = HTTPStatus.OK
        kwargs = {}

        wrapped = mock.AsyncMock(return_value=mock.Mock(status=status))

        with patch_tracer, patch_attr, patch_thread:
            await trace.wrap_session_request(
                wrapped, "ClientSession._request", (http_method, http_url), kwargs
            )

        expected_attributes = {
            "component": "HTTP",
            "http.host": http_host,
            "http.method": http_method,
            "http.path": http_path,
            "http.status_code": status,
            "http.url": http_url,
        }
        expected_name = http_path
        expected_status = status_module.Status(0)

        self.assertEqual(SpanKind.CLIENT, mock_tracer._span.span_kind)
        self.assertEqual(expected_attributes, mock_tracer._span.attributes)
        self.assertEqual(expected_name, mock_tracer._span.name)
        self.assertEqual(expected_status.__dict__, mock_tracer._span.status.__dict__)

    async def test_wrap_session_request_excludelist_nok(self):
        async def wrapped(*args, **kwargs):
            result = mock.Mock()
            result.status = HTTPStatus.OK
            return result

        mock_tracer = MockTracer()

        patch_tracer = mock.patch(
            "opencensus.ext.requests.trace.execution_context." "get_opencensus_tracer",
            return_value=mock_tracer,
        )
        patch_attr = mock.patch(
            "opencensus.ext.requests.trace.execution_context." "get_opencensus_attr",
            return_value=["localhost:8080"],
        )
        patch_thread = mock.patch(
            "opencensus.ext.requests.trace.execution_context." "is_exporter",
            return_value=False,
        )

        http_host = "localhost:8080"
        http_path = "/test"
        http_url = f"http://{http_host}{http_path}"
        http_method = "POST"
        kwargs = {}

        with patch_tracer, patch_attr, patch_thread:
            await trace.wrap_session_request(
                wrapped, "ClientSession._request", (http_method, http_url), kwargs
            )

        self.assertEqual(None, mock_tracer._span)

    async def test_wrap_session_request_exporter_thread(self):
        async def wrapped(*args, **kwargs):
            result = mock.Mock()
            result.status = HTTPStatus.OK
            return result

        mock_tracer = MockTracer()

        patch_tracer = mock.patch(
            "opencensus.ext.requests.trace.execution_context." "get_opencensus_tracer",
            return_value=mock_tracer,
        )
        patch_attr = mock.patch(
            "opencensus.ext.requests.trace.execution_context." "get_opencensus_attr",
            return_value=["localhost:8080"],
        )
        patch_thread = mock.patch(
            "opencensus.ext.requests.trace.execution_context." "is_exporter",
            return_value=True,
        )

        http_host = "localhost:8080"
        http_path = "/test"
        http_url = f"http://{http_host}{http_path}"
        http_method = "POST"
        kwargs = {}

        with patch_tracer, patch_attr, patch_thread:
            await trace.wrap_session_request(
                wrapped, "ClientSession._request", (http_method, http_url), kwargs
            )

        self.assertEqual(None, mock_tracer._span)

    async def test_header_is_passed_in(self):
        wrapped = mock.AsyncMock(return_value=mock.Mock(status=HTTPStatus.OK))
        mock_tracer = MockTracer(
            propagator=mock.Mock(
                to_headers=lambda span_context: {"x-trace": "some-value"}
            )
        )

        patch_tracer = mock.patch(
            "opencensus.ext.requests.trace.execution_context." "get_opencensus_tracer",
            return_value=mock_tracer,
        )
        patch_thread = mock.patch(
            "opencensus.ext.requests.trace.execution_context." "is_exporter",
            return_value=False,
        )

        http_host = "localhost:8080"
        http_path = "/test"
        http_url = f"http://{http_host}{http_path}"
        http_method = "POST"
        kwargs = {}

        with patch_tracer, patch_thread:
            await trace.wrap_session_request(
                wrapped, "ClientSession._request", (http_method, http_url), kwargs
            )

        self.assertEqual(kwargs["headers"]["x-trace"], "some-value")

    async def test_headers_are_preserved(self):
        wrapped = mock.AsyncMock(return_value=mock.Mock(status=HTTPStatus.OK))
        mock_tracer = MockTracer(
            propagator=mock.Mock(
                to_headers=lambda span_context: {"x-trace": "some-value"}
            )
        )

        patch_tracer = mock.patch(
            "opencensus.ext.requests.trace.execution_context." "get_opencensus_tracer",
            return_value=mock_tracer,
        )
        patch_thread = mock.patch(
            "opencensus.ext.requests.trace.execution_context." "is_exporter",
            return_value=False,
        )

        http_host = "localhost:8080"
        http_path = "/test"
        http_url = f"http://{http_host}{http_path}"
        http_method = "POST"
        kwargs = {"headers": {"key": "value"}}

        with patch_tracer, patch_thread:
            await trace.wrap_session_request(
                wrapped, "ClientSession._request", (http_method, http_url), kwargs
            )

        self.assertEqual(kwargs["headers"]["key"], "value")
        self.assertEqual(kwargs["headers"]["x-trace"], "some-value")

    async def test_tracer_headers_are_overwritten(self):
        wrapped = mock.AsyncMock(return_value=mock.Mock(status=HTTPStatus.OK))
        mock_tracer = MockTracer(
            propagator=mock.Mock(
                to_headers=lambda span_context: {"x-trace": "some-value"}
            )
        )

        patch_tracer = mock.patch(
            "opencensus.ext.requests.trace.execution_context." "get_opencensus_tracer",
            return_value=mock_tracer,
        )

        patch_thread = mock.patch(
            "opencensus.ext.requests.trace.execution_context." "is_exporter",
            return_value=False,
        )

        http_host = "localhost:8080"
        http_path = "/test"
        http_url = f"http://{http_host}{http_path}"
        http_method = "POST"
        kwargs = {"headers": {"x-trace": "original-value"}}

        with patch_tracer, patch_thread:
            await trace.wrap_session_request(
                wrapped, "ClientSession._request", (http_method, http_url), kwargs
            )

        self.assertEqual(kwargs["headers"]["x-trace"], "some-value")

    async def test_wrap_session_request_timeout(self):
        http_host = "localhost:8080"
        http_path = "/test"
        http_url = f"http://{http_host}{http_path}"
        http_method = "POST"
        status = HTTPStatus.OK
        kwargs = {}

        wrapped = mock.AsyncMock(return_value=mock.Mock(status=status))
        wrapped.side_effect = asyncio.TimeoutError()

        mock_tracer = MockTracer(
            propagator=mock.Mock(
                to_headers=lambda span_context: {"x-trace": "some-value"}
            )
        )
        patch_tracer = mock.patch(
            "opencensus.ext.requests.trace.execution_context." "get_opencensus_tracer",
            return_value=mock_tracer,
        )
        patch_thread = mock.patch(
            "opencensus.ext.requests.trace.execution_context." "is_exporter",
            return_value=False,
        )

        with patch_tracer, patch_thread:
            with self.assertRaises(asyncio.TimeoutError):
                await trace.wrap_session_request(
                    wrapped, "ClientSession._request", (http_method, http_url), kwargs
                )

        expected_attributes = {
            "component": "HTTP",
            "http.host": http_host,
            "http.method": http_method,
            "http.path": http_path,
            "http.url": http_url,
        }
        expected_name = http_path
        expected_status = status_module.Status(4, "request timed out")

        self.assertEqual(SpanKind.CLIENT, mock_tracer._span.span_kind)
        self.assertEqual(expected_attributes, mock_tracer._span.attributes)
        self.assertEqual(kwargs["headers"]["x-trace"], "some-value")
        self.assertEqual(expected_name, mock_tracer._span.name)
        self.assertEqual(expected_status.__dict__, mock_tracer._span.status.__dict__)

    async def test_wrap_session_request_invalid_url(self):
        http_host = "localhost:8080"
        http_path = "/test"
        http_url = f"http://{http_host}{http_path}"
        http_method = "POST"
        status = HTTPStatus.OK
        kwargs = {}

        wrapped = mock.AsyncMock(return_value=mock.Mock(status=status))
        wrapped.side_effect = InvalidURL(url=http_url)

        mock_tracer = MockTracer(
            propagator=mock.Mock(
                to_headers=lambda span_context: {"x-trace": "some-value"}
            )
        )

        patch_tracer = mock.patch(
            "opencensus.ext.requests.trace.execution_context." "get_opencensus_tracer",
            return_value=mock_tracer,
        )
        patch_thread = mock.patch(
            "opencensus.ext.requests.trace.execution_context." "is_exporter",
            return_value=False,
        )

        with patch_tracer, patch_thread:
            with self.assertRaises(InvalidURL):
                await trace.wrap_session_request(
                    wrapped, "ClientSession._request", (http_method, http_url), kwargs
                )

        expected_attributes = {
            "component": "HTTP",
            "http.host": http_host,
            "http.method": http_method,
            "http.path": http_path,
            "http.url": http_url,
        }
        expected_name = http_path
        expected_status = status_module.Status(3, "invalid URL")

        self.assertEqual(SpanKind.CLIENT, mock_tracer._span.span_kind)
        self.assertEqual(expected_attributes, mock_tracer._span.attributes)
        self.assertEqual(kwargs["headers"]["x-trace"], "some-value")
        self.assertEqual(expected_name, mock_tracer._span.name)
        self.assertEqual(expected_status.__dict__, mock_tracer._span.status.__dict__)

    async def test_wrap_session_request_exception(self):
        http_host = "localhost:8080"
        http_path = "/test"
        http_url = f"http://{http_host}{http_path}"
        http_method = "POST"
        status = HTTPStatus.OK
        kwargs = {}

        wrapped = mock.AsyncMock(return_value=mock.Mock(status=status))
        wrapped.side_effect = ClientPayloadError()

        mock_tracer = MockTracer(
            propagator=mock.Mock(
                to_headers=lambda span_context: {"x-trace": "some-value"}
            )
        )
        patch_tracer = mock.patch(
            "opencensus.ext.requests.trace.execution_context." "get_opencensus_tracer",
            return_value=mock_tracer,
        )
        patch_thread = mock.patch(
            "opencensus.ext.requests.trace.execution_context." "is_exporter",
            return_value=False,
        )

        with patch_tracer, patch_thread:
            with self.assertRaises(ClientPayloadError):
                await trace.wrap_session_request(
                    wrapped, "ClientSession._request", (http_method, http_url), kwargs
                )

        expected_attributes = {
            "component": "HTTP",
            "http.host": http_host,
            "http.method": http_method,
            "http.path": http_path,
            "http.url": http_url,
        }
        expected_name = http_path
        expected_status = status_module.Status(2, "")

        self.assertEqual(SpanKind.CLIENT, mock_tracer._span.span_kind)
        self.assertEqual(expected_attributes, mock_tracer._span.attributes)
        self.assertEqual(kwargs["headers"]["x-trace"], "some-value")
        self.assertEqual(expected_name, mock_tracer._span.name)
        self.assertEqual(expected_status.__dict__, mock_tracer._span.status.__dict__)


class MockSpan(object):
    def __init__(self, name: str):
        self.name = name
        self.attributes = {}
        self.span_kind = None
        self.status = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def set_status(self, status):
        self.status = status

    def add_attribute(self, attribute_key, attribute_value) -> None:
        self.attributes[attribute_key] = attribute_value


class MockTracer(object):
    def __init__(self, propagator=None):
        self._span = None
        self.span_context = {}
        self.propagator = propagator

    def span(self, name):
        if self._span is None:
            self._span = MockSpan(name=name)
        return self._span
