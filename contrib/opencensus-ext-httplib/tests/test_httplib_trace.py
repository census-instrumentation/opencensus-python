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

from opencensus.ext.httplib import trace
from opencensus.trace import span as span_module
from opencensus.trace.propagation import trace_context_http_header_format


class Test_httplib_trace(unittest.TestCase):
    def tearDown(self):
        from opencensus.trace import execution_context

        execution_context.clear()

    def test_trace_integration(self):
        mock_wrap_request = mock.Mock()
        mock_wrap_response = mock.Mock()
        mock_httplib = mock.Mock()

        wrap_request_result = 'wrap request result'
        wrap_response_result = 'wrap response result'
        mock_wrap_request.return_value = wrap_request_result
        mock_wrap_response.return_value = wrap_response_result

        mock_request_func = mock.Mock()
        mock_response_func = mock.Mock()
        mock_request_func.__name__ = 'request'
        mock_response_func.__name__ = 'getresponse'
        setattr(mock_httplib.HTTPConnection, 'request', mock_request_func)
        setattr(mock_httplib.HTTPConnection, 'getresponse', mock_response_func)

        patch_wrap_request = mock.patch(
            'opencensus.ext.httplib.trace.wrap_httplib_request',
            mock_wrap_request)
        patch_wrap_response = mock.patch(
            'opencensus.ext.httplib.trace.wrap_httplib_response',
            mock_wrap_response)
        patch_httplib = mock.patch(
            'opencensus.ext.httplib.trace.httplib', mock_httplib)

        with patch_wrap_request, patch_wrap_response, patch_httplib:
            trace.trace_integration()

        self.assertEqual(
            getattr(mock_httplib.HTTPConnection, 'request'),
            wrap_request_result)
        self.assertEqual(
            getattr(mock_httplib.HTTPConnection, 'getresponse'),
            wrap_response_result)

    def test_wrap_httplib_request(self):
        mock_span = mock.Mock()
        span_id = '1234'
        mock_span.span_id = span_id
        mock_tracer = MockTracer(mock_span)
        mock_request_func = mock.Mock()
        mock_request_func.__name__ = 'request'

        patch = mock.patch(
            'opencensus.ext.requests.trace.execution_context.'
            'get_opencensus_tracer',
            return_value=mock_tracer)

        wrapped = trace.wrap_httplib_request(mock_request_func)

        mock_self = mock.Mock()
        method = 'GET'
        url = 'http://localhost:8080'
        body = None
        headers = {}

        with patch:
            wrapped(mock_self, method, url, body, headers)

        expected_attributes = {'http.url': url, 'http.method': method}
        expected_name = '[httplib]request'

        mock_request_func.assert_called_with(mock_self, method, url, body, {
            'traceparent': '00-123-456-01',
        })
        self.assertEqual(expected_attributes, mock_tracer.span.attributes)
        self.assertEqual(expected_name, mock_tracer.span.name)
        self.assertEqual(span_module.SpanKind.CLIENT,
                         mock_tracer.span.span_kind)

    def test_wrap_httplib_request_blacklist_ok(self):
        mock_span = mock.Mock()
        span_id = '1234'
        mock_span.span_id = span_id
        mock_tracer = MockTracer(mock_span)
        mock_request_func = mock.Mock()
        mock_request_func.__name__ = 'request'

        patch_tracer = mock.patch(
            'opencensus.ext.requests.trace.execution_context.'
            'get_opencensus_tracer',
            return_value=mock_tracer)
        patch_attr = mock.patch(
            'opencensus.ext.requests.trace.execution_context.'
            'get_opencensus_attr',
            return_value=None)

        wrapped = trace.wrap_httplib_request(mock_request_func)

        mock_self = mock.Mock()
        method = 'GET'
        url = 'http://localhost:8080'
        body = None
        headers = {}

        with patch_tracer, patch_attr:
            wrapped(mock_self, method, url, body, headers)

        mock_request_func.assert_called_with(mock_self, method, url, body, {
            'traceparent': '00-123-456-01',
        })

    def test_wrap_httplib_request_blacklist_nok(self):
        mock_span = mock.Mock()
        span_id = '1234'
        mock_span.span_id = span_id
        mock_tracer = MockTracer(mock_span)
        mock_request_func = mock.Mock()
        mock_request_func.__name__ = 'request'

        patch_tracer = mock.patch(
            'opencensus.ext.requests.trace.execution_context.'
            'get_opencensus_tracer',
            return_value=mock_tracer)
        patch_attr = mock.patch(
            'opencensus.ext.requests.trace.execution_context.'
            'get_opencensus_attr',
            return_value=['localhost:8080'])

        wrapped = trace.wrap_httplib_request(mock_request_func)

        mock_self = mock.Mock()
        mock_self._dns_host = 'localhost'
        mock_self.port = '8080'
        method = 'GET'
        url = 'http://{}:{}'.format(mock_self._dns_host, mock_self.port)
        body = None
        headers = {}

        with patch_tracer, patch_attr:
            wrapped(mock_self, method, url, body, headers)

        mock_request_func.assert_called_with(mock_self, method, url, body, {})

    def test_wrap_httplib_response(self):
        mock_span = mock.Mock()
        span_id = '1234'
        mock_span.span_id = span_id
        mock_span.attributes = {}
        mock_tracer = MockTracer(mock_span)
        mock_response_func = mock.Mock()
        mock_result = mock.Mock()
        mock_result.status = '200'
        mock_response_func.return_value = mock_result

        patch_tracer = mock.patch(
            'opencensus.ext.requests.trace.execution_context.'
            'get_opencensus_tracer',
            return_value=mock_tracer)
        patch_attr = mock.patch(
            'opencensus.ext.httplib.trace.'
            'execution_context.get_opencensus_attr',
            return_value=span_id)

        wrapped = trace.wrap_httplib_response(mock_response_func)

        with patch_tracer, patch_attr:
            wrapped(mock.Mock())

        expected_attributes = {'http.status_code': '200'}

        self.assertEqual(expected_attributes, mock_tracer.span.attributes)

    def test_wrap_httplib_response_no_open_span(self):
        mock_span = mock.Mock()
        span_id = '1234'
        mock_span.span_id = span_id
        mock_span.attributes = {}
        mock_tracer = MockTracer(mock_span)
        mock_response_func = mock.Mock()
        mock_result = mock.Mock()
        mock_result.status = '200'
        mock_response_func.return_value = mock_result

        patch_tracer = mock.patch(
            'opencensus.ext.requests.trace.execution_context.'
            'get_opencensus_tracer',
            return_value=mock_tracer)
        patch_attr = mock.patch(
            'opencensus.ext.httplib.trace.'
            'execution_context.get_opencensus_attr',
            return_value='1111')

        wrapped = trace.wrap_httplib_response(mock_response_func)

        with patch_tracer, patch_attr:
            wrapped(mock.Mock())

        # Attribute should be empty as there is no matching span
        expected_attributes = {}

        self.assertEqual(expected_attributes, mock_tracer.span.attributes)


class MockTracer(object):
    def __init__(self, span=None):
        self.span = span
        self.propagator = (
            trace_context_http_header_format.TraceContextPropagator())

    def current_span(self):
        return self.span

    def start_span(self):
        span = mock.Mock()
        span.attributes = {}
        span.context_tracer = mock.Mock()
        span.context_tracer.span_context = mock.Mock()
        span.context_tracer.span_context.trace_id = '123'
        span.context_tracer.span_context.span_id = '456'
        span.context_tracer.span_context.tracestate = None
        self.span = span
        return span

    def end_span(self):
        pass

    def add_attribute_to_current_span(self, key, value):
        self.span.attributes[key] = value
