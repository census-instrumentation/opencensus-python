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

from opencensus.trace import span as span_module
from opencensus.trace.ext.requests import trace


class Test_requests_trace(unittest.TestCase):

    def test_trace_integration(self):
        mock_wrap = mock.Mock()
        mock_requests = mock.Mock()

        wrap_result = 'wrap result'
        mock_wrap.return_value = wrap_result

        for func in trace.REQUESTS_WRAP_METHODS:
            mock_func = mock.Mock()
            mock_func.__name__ = func
            setattr(mock_requests, func, mock_func)

        patch_wrap = mock.patch(
            'opencensus.trace.ext.requests.trace.wrap_requests', mock_wrap)
        patch_requests = mock.patch(
            'opencensus.trace.ext.requests.trace.requests', mock_requests)

        with patch_wrap, patch_requests:
            trace.trace_integration()

        for func in trace.REQUESTS_WRAP_METHODS:
            self.assertEqual(getattr(mock_requests, func), wrap_result)

    def test_wrap_requests(self):
        mock_return = mock.Mock()
        mock_return.status_code = 200
        return_value = mock_return
        mock_func = mock.Mock()
        mock_func.__name__ = 'get'
        mock_func.return_value = return_value
        mock_tracer = MockTracer()

        patch = mock.patch(
            'opencensus.trace.ext.requests.trace.execution_context.'
            'get_opencensus_tracer',
            return_value=mock_tracer)

        wrapped = trace.wrap_requests(mock_func)

        url = 'http://localhost:8080'

        with patch:
            wrapped(url)

        expected_attributes = {
            'http.url': url,
            'http.status_code': '200'}
        expected_name = '[requests]get'

        self.assertEqual(span_module.SpanKind.CLIENT,
                         mock_tracer.current_span.span_kind)
        self.assertEqual(expected_attributes,
                         mock_tracer.current_span.attributes)
        self.assertEqual(expected_name, mock_tracer.current_span.name)

    def test_wrap_session_request(self):
        wrapped = mock.Mock(return_value=mock.Mock(status_code=200))

        mock_tracer = MockTracer(propagator=mock.Mock(
            to_headers= lambda x: {'x-trace': 'some-value'})
        )

        patch = mock.patch(
            'opencensus.trace.ext.requests.trace.execution_context.'
            'get_opencensus_tracer',
            return_value=mock_tracer)

        url = 'http://localhost:8080'
        request_method = 'POST'
        kwargs = {}

        with patch:
            result = trace.wrap_session_request(
                wrapped, 'Session.request', (request_method, url), kwargs)

        expected_attributes = {
            'http.url': url,
            'http.status_code': '200'}
        expected_name = '[requests]POST'

        self.assertEqual(span_module.SpanKind.CLIENT,
                         mock_tracer.current_span.span_kind)
        self.assertEqual(expected_attributes,
                         mock_tracer.current_span.attributes)
        self.assertEqual(kwargs['headers']['x-trace'], 'some-value')
        self.assertEqual(expected_name, mock_tracer.current_span.name)

    def test_header_is_passed_in(self):
        wrapped = mock.Mock(return_value=mock.Mock(status_code=200))
        mock_tracer = MockTracer(propagator=mock.Mock(
            to_headers= lambda x: {'x-trace': 'some-value'})
        )
        
        patch = mock.patch(
            'opencensus.trace.ext.requests.trace.execution_context.'
            'get_opencensus_tracer',
            return_value=mock_tracer)

        url = 'http://localhost:8080'
        request_method = 'POST'
        kwargs = {}

        with patch:
            result = trace.wrap_session_request(
                wrapped, 'Session.request', (request_method, url), kwargs)

        self.assertEqual(kwargs['headers']['x-trace'], 'some-value')

    def test_headers_are_preserved(self):
        wrapped = mock.Mock(return_value=mock.Mock(status_code=200))
        mock_tracer = MockTracer(propagator=mock.Mock(
            to_headers= lambda x: {'x-trace': 'some-value'})
        )

        patch = mock.patch(
            'opencensus.trace.ext.requests.trace.execution_context.'
            'get_opencensus_tracer',
            return_value=mock_tracer)

        url = 'http://localhost:8080'
        request_method = 'POST'
        kwargs = {'headers': {'key': 'value'}}

        with patch:
            result = trace.wrap_session_request(
                wrapped, 'Session.request', (request_method, url), kwargs)

        self.assertEqual(kwargs['headers']['key'], 'value')
        self.assertEqual(kwargs['headers']['x-trace'], 'some-value')


    def test_tracer_headers_are_overwritten(self):
        wrapped = mock.Mock(return_value=mock.Mock(status_code=200))
        mock_tracer = MockTracer(propagator=mock.Mock(
            to_headers= lambda x: {'x-trace': 'some-value'})
        )

        patch = mock.patch(
            'opencensus.trace.ext.requests.trace.execution_context.'
            'get_opencensus_tracer',
            return_value=mock_tracer)

        url = 'http://localhost:8080'
        request_method = 'POST'
        kwargs = {'headers': {'x-trace': 'original-value'}}

        with patch:
            result = trace.wrap_session_request(
                wrapped, 'Session.request', (request_method, url), kwargs)

        self.assertEqual(kwargs['headers']['x-trace'], 'some-value')

class MockTracer(object):
    def __init__(self, propagator=None):
        self.current_span = None
        self.span_context = {}
        self.propagator = propagator

    def start_span(self):
        span = mock.Mock()
        span.attributes = {}
        self.current_span = span
        return span

    def end_span(self):
        pass

    def add_attribute_to_current_span(self, key, value):
        self.current_span.attributes[key] = value
