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
import requests
from opencensus.trace.tracers import noop_tracer

from opencensus.ext.requests import trace
from opencensus.trace import span as span_module, execution_context
from opencensus.trace import status as status_module


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
            'opencensus.ext.requests.trace.wrap_requests', mock_wrap)
        patch_requests = mock.patch(
            'opencensus.ext.requests.trace.requests', mock_requests)

        with patch_wrap, patch_requests:
            trace.trace_integration()

            self.assertIsInstance(execution_context.get_opencensus_tracer(),
                                  noop_tracer.NoopTracer)

        for func in trace.REQUESTS_WRAP_METHODS:
            self.assertEqual(getattr(mock_requests, func), wrap_result)

    def test_trace_integration_set_tracer(self):
        mock_wrap = mock.Mock()
        mock_requests = mock.Mock()

        wrap_result = 'wrap result'
        mock_wrap.return_value = wrap_result

        for func in trace.REQUESTS_WRAP_METHODS:
            mock_func = mock.Mock()
            mock_func.__name__ = func
            setattr(mock_requests, func, mock_func)

        patch_wrap = mock.patch(
            'opencensus.ext.requests.trace.wrap_requests', mock_wrap)
        patch_requests = mock.patch(
            'opencensus.ext.requests.trace.requests', mock_requests)

        class TmpTracer(noop_tracer.NoopTracer):
            pass

        with patch_wrap, patch_requests:
            trace.trace_integration(tracer=TmpTracer())

            self.assertIsInstance(execution_context.get_opencensus_tracer(),
                                  TmpTracer)

    def test_wrap_requests(self):
        mock_return = mock.Mock()
        mock_return.status_code = 200
        return_value = mock_return
        mock_func = mock.Mock()
        mock_func.__name__ = 'get'
        mock_func.return_value = return_value
        mock_tracer = MockTracer()

        patch = mock.patch(
            'opencensus.ext.requests.trace.execution_context.'
            'get_opencensus_tracer',
            return_value=mock_tracer)

        patch_thread = mock.patch(
            'opencensus.ext.requests.trace.execution_context.'
            'is_exporter',
            return_value=False)

        wrapped = trace.wrap_requests(mock_func)

        url = 'http://localhost:8080/test'

        with patch, patch_thread:
            wrapped(url)

        expected_attributes = {
            'http.host': 'localhost:8080',
            'http.method': 'GET',
            'http.path': '/test',
            'http.status_code': 200,
            'http.url': url,
        }
        expected_name = '/test'
        expected_status = status_module.Status(0)

        self.assertEqual(span_module.SpanKind.CLIENT,
                         mock_tracer.current_span.span_kind)
        self.assertEqual(expected_attributes,
                         mock_tracer.current_span.attributes)
        self.assertEqual(expected_name, mock_tracer.current_span.name)
        self.assertEqual(
            expected_status.__dict__,
            mock_tracer.current_span.status.__dict__
        )

    def test_wrap_requests_blacklist_ok(self):
        mock_return = mock.Mock()
        mock_return.status_code = 200
        return_value = mock_return
        mock_func = mock.Mock()
        mock_func.__name__ = 'get'
        mock_func.return_value = return_value
        mock_tracer = MockTracer()

        patch_tracer = mock.patch(
            'opencensus.ext.requests.trace.execution_context.'
            'get_opencensus_tracer',
            return_value=mock_tracer)
        patch_attr = mock.patch(
            'opencensus.ext.requests.trace.execution_context.'
            'get_opencensus_attr',
            return_value=['localhost:8080'])
        patch_thread = mock.patch(
            'opencensus.ext.requests.trace.execution_context.'
            'is_exporter',
            return_value=False)

        wrapped = trace.wrap_requests(mock_func)

        url = 'http://localhost'

        with patch_tracer, patch_attr, patch_thread:
            wrapped(url)

        expected_name = '/'

        self.assertEqual(expected_name, mock_tracer.current_span.name)

    def test_wrap_requests_blacklist_nok(self):
        mock_return = mock.Mock()
        mock_return.status_code = 200
        return_value = mock_return
        mock_func = mock.Mock()
        mock_func.__name__ = 'get'
        mock_func.return_value = return_value
        mock_tracer = MockTracer()

        patch_tracer = mock.patch(
            'opencensus.ext.requests.trace.execution_context.'
            'get_opencensus_tracer',
            return_value=mock_tracer)
        patch_attr = mock.patch(
            'opencensus.ext.requests.trace.execution_context.'
            'get_opencensus_attr',
            return_value=['localhost:8080'])
        patch_thread = mock.patch(
            'opencensus.ext.requests.trace.execution_context.'
            'is_exporter',
            return_value=False)

        wrapped = trace.wrap_requests(mock_func)

        url = 'http://localhost:8080'

        with patch_tracer, patch_attr, patch_thread:
            wrapped(url)

        self.assertEqual(None, mock_tracer.current_span)

    def test_wrap_requests_exporter_thread(self):
        mock_return = mock.Mock()
        mock_return.status_code = 200
        return_value = mock_return
        mock_func = mock.Mock()
        mock_func.__name__ = 'get'
        mock_func.return_value = return_value
        mock_tracer = MockTracer()

        patch_tracer = mock.patch(
            'opencensus.ext.requests.trace.execution_context.'
            'get_opencensus_tracer',
            return_value=mock_tracer)
        patch_attr = mock.patch(
            'opencensus.ext.requests.trace.execution_context.'
            'get_opencensus_attr',
            return_value=['localhost:8080'])
        patch_thread = mock.patch(
            'opencensus.ext.requests.trace.execution_context.'
            'is_exporter',
            return_value=True)

        wrapped = trace.wrap_requests(mock_func)

        url = 'http://localhost:8080'

        with patch_tracer, patch_attr, patch_thread:
            wrapped(url)

        self.assertEqual(None, mock_tracer.current_span)

    def test_wrap_requests_timeout(self):
        mock_return = mock.Mock()
        mock_return.status_code = 200
        return_value = mock_return
        mock_func = mock.Mock()
        mock_func.__name__ = 'get'
        mock_func.return_value = return_value
        mock_func.side_effect = requests.Timeout
        mock_tracer = MockTracer()

        patch = mock.patch(
            'opencensus.ext.requests.trace.execution_context.'
            'get_opencensus_tracer',
            return_value=mock_tracer)

        patch_thread = mock.patch(
            'opencensus.ext.requests.trace.execution_context.'
            'is_exporter',
            return_value=False)

        wrapped = trace.wrap_requests(mock_func)

        url = 'http://localhost:8080/test'

        with patch, patch_thread:
            wrapped(url)

        expected_attributes = {
            'http.host': 'localhost:8080',
            'http.method': 'GET',
            'http.path': '/test',
            'http.url': url,
        }
        expected_name = '/test'
        expected_status = status_module.Status(4, 'request timed out')

        self.assertEqual(span_module.SpanKind.CLIENT,
                         mock_tracer.current_span.span_kind)
        self.assertEqual(expected_attributes,
                         mock_tracer.current_span.attributes)
        self.assertEqual(expected_name, mock_tracer.current_span.name)
        self.assertEqual(
            expected_status.__dict__,
            mock_tracer.current_span.status.__dict__
        )

    def test_wrap_requests_invalid_url(self):
        mock_return = mock.Mock()
        mock_return.status_code = 200
        return_value = mock_return
        mock_func = mock.Mock()
        mock_func.__name__ = 'get'
        mock_func.return_value = return_value
        mock_func.side_effect = requests.URLRequired
        mock_tracer = MockTracer()

        patch = mock.patch(
            'opencensus.ext.requests.trace.execution_context.'
            'get_opencensus_tracer',
            return_value=mock_tracer)

        patch_thread = mock.patch(
            'opencensus.ext.requests.trace.execution_context.'
            'is_exporter',
            return_value=False)

        wrapped = trace.wrap_requests(mock_func)

        url = 'http://localhost:8080/test'

        with patch, patch_thread:
            wrapped(url)

        expected_attributes = {
            'http.host': 'localhost:8080',
            'http.method': 'GET',
            'http.path': '/test',
            'http.url': url,
        }
        expected_name = '/test'
        expected_status = status_module.Status(3, 'invalid URL')

        self.assertEqual(span_module.SpanKind.CLIENT,
                         mock_tracer.current_span.span_kind)
        self.assertEqual(expected_attributes,
                         mock_tracer.current_span.attributes)
        self.assertEqual(expected_name, mock_tracer.current_span.name)
        self.assertEqual(
            expected_status.__dict__,
            mock_tracer.current_span.status.__dict__
        )

    def test_wrap_requests_exception(self):
        mock_return = mock.Mock()
        mock_return.status_code = 200
        return_value = mock_return
        mock_func = mock.Mock()
        mock_func.__name__ = 'get'
        mock_func.return_value = return_value
        mock_func.side_effect = requests.TooManyRedirects
        mock_tracer = MockTracer()

        patch = mock.patch(
            'opencensus.ext.requests.trace.execution_context.'
            'get_opencensus_tracer',
            return_value=mock_tracer)

        patch_thread = mock.patch(
            'opencensus.ext.requests.trace.execution_context.'
            'is_exporter',
            return_value=False)

        wrapped = trace.wrap_requests(mock_func)

        url = 'http://localhost:8080/test'

        with patch, patch_thread:
            wrapped(url)

        expected_attributes = {
            'http.host': 'localhost:8080',
            'http.method': 'GET',
            'http.path': '/test',
            'http.url': url,
        }
        expected_name = '/test'
        expected_status = status_module.Status(2, '')

        self.assertEqual(span_module.SpanKind.CLIENT,
                         mock_tracer.current_span.span_kind)
        self.assertEqual(expected_attributes,
                         mock_tracer.current_span.attributes)
        self.assertEqual(expected_name, mock_tracer.current_span.name)
        self.assertEqual(
            expected_status.__dict__,
            mock_tracer.current_span.status.__dict__
        )

    def test_wrap_session_request(self):
        wrapped = mock.Mock(return_value=mock.Mock(status_code=200))

        mock_tracer = MockTracer(
            propagator=mock.Mock(
                to_headers=lambda x: {'x-trace': 'some-value'}))

        patch = mock.patch(
            'opencensus.ext.requests.trace.execution_context.'
            'get_opencensus_tracer',
            return_value=mock_tracer)
        patch_thread = mock.patch(
            'opencensus.ext.requests.trace.execution_context.'
            'is_exporter',
            return_value=False)

        url = 'http://localhost:8080/test'
        request_method = 'POST'
        kwargs = {}

        with patch, patch_thread:
            trace.wrap_session_request(wrapped, 'Session.request',
                                       (request_method, url), kwargs)

        expected_attributes = {
            'http.host': 'localhost:8080',
            'http.method': 'POST',
            'http.path': '/test',
            'http.status_code': 200,
            'http.url': url,
        }
        expected_name = '/test'
        expected_status = status_module.Status(0)

        self.assertEqual(span_module.SpanKind.CLIENT,
                         mock_tracer.current_span.span_kind)
        self.assertEqual(expected_attributes,
                         mock_tracer.current_span.attributes)
        self.assertEqual(kwargs['headers']['x-trace'], 'some-value')
        self.assertEqual(expected_name, mock_tracer.current_span.name)
        self.assertEqual(
            expected_status.__dict__,
            mock_tracer.current_span.status.__dict__
        )

    def test_wrap_session_request_blacklist_ok(self):
        def wrapped(*args, **kwargs):
            result = mock.Mock()
            result.status_code = 200
            return result

        mock_tracer = MockTracer(
            propagator=mock.Mock(
                to_headers=lambda x: {'x-trace': 'some-value'}))

        patch_tracer = mock.patch(
            'opencensus.ext.requests.trace.execution_context.'
            'get_opencensus_tracer',
            return_value=mock_tracer)
        patch_attr = mock.patch(
            'opencensus.ext.requests.trace.execution_context.'
            'get_opencensus_attr',
            return_value=None)
        patch_thread = mock.patch(
            'opencensus.ext.requests.trace.execution_context.'
            'is_exporter',
            return_value=False)

        url = 'http://localhost/'
        request_method = 'POST'

        with patch_tracer, patch_attr, patch_thread:
            trace.wrap_session_request(wrapped, 'Session.request',
                                       (request_method, url), {})

        expected_name = '/'
        self.assertEqual(expected_name, mock_tracer.current_span.name)

    def test_wrap_session_request_blacklist_nok(self):
        def wrapped(*args, **kwargs):
            result = mock.Mock()
            result.status_code = 200
            return result

        mock_tracer = MockTracer()

        patch_tracer = mock.patch(
            'opencensus.ext.requests.trace.execution_context.'
            'get_opencensus_tracer',
            return_value=mock_tracer)
        patch_attr = mock.patch(
            'opencensus.ext.requests.trace.execution_context.'
            'get_opencensus_attr',
            return_value=['localhost:8080'])
        patch_thread = mock.patch(
            'opencensus.ext.requests.trace.execution_context.'
            'is_exporter',
            return_value=False)

        url = 'http://localhost:8080'
        request_method = 'POST'

        with patch_tracer, patch_attr, patch_thread:
            trace.wrap_session_request(wrapped, 'Session.request',
                                       (request_method, url), {})
        self.assertEqual(None, mock_tracer.current_span)

    def test_wrap_session_request_exporter_thread(self):
        def wrapped(*args, **kwargs):
            result = mock.Mock()
            result.status_code = 200
            return result

        mock_tracer = MockTracer()

        patch_tracer = mock.patch(
            'opencensus.ext.requests.trace.execution_context.'
            'get_opencensus_tracer',
            return_value=mock_tracer)
        patch_attr = mock.patch(
            'opencensus.ext.requests.trace.execution_context.'
            'get_opencensus_attr',
            return_value=['localhost:8080'])
        patch_thread = mock.patch(
            'opencensus.ext.requests.trace.execution_context.'
            'is_exporter',
            return_value=True)

        url = 'http://localhost:8080'
        request_method = 'POST'

        with patch_tracer, patch_attr, patch_thread:
            trace.wrap_session_request(wrapped, 'Session.request',
                                       (request_method, url), {})
        self.assertEqual(None, mock_tracer.current_span)

    def test_header_is_passed_in(self):
        wrapped = mock.Mock(return_value=mock.Mock(status_code=200))
        mock_tracer = MockTracer(
            propagator=mock.Mock(
                to_headers=lambda x: {'x-trace': 'some-value'}))

        patch = mock.patch(
            'opencensus.ext.requests.trace.execution_context.'
            'get_opencensus_tracer',
            return_value=mock_tracer)
        patch_thread = mock.patch(
            'opencensus.ext.requests.trace.execution_context.'
            'is_exporter',
            return_value=False)

        url = 'http://localhost:8080'
        request_method = 'POST'
        kwargs = {}

        with patch, patch_thread:
            trace.wrap_session_request(wrapped, 'Session.request',
                                       (request_method, url), kwargs)

        self.assertEqual(kwargs['headers']['x-trace'], 'some-value')

    def test_headers_are_preserved(self):
        wrapped = mock.Mock(return_value=mock.Mock(status_code=200))
        mock_tracer = MockTracer(
            propagator=mock.Mock(
                to_headers=lambda x: {'x-trace': 'some-value'}))

        patch = mock.patch(
            'opencensus.ext.requests.trace.execution_context.'
            'get_opencensus_tracer',
            return_value=mock_tracer)
        patch_thread = mock.patch(
            'opencensus.ext.requests.trace.execution_context.'
            'is_exporter',
            return_value=False)

        url = 'http://localhost:8080'
        request_method = 'POST'
        kwargs = {'headers': {'key': 'value'}}

        with patch, patch_thread:
            trace.wrap_session_request(wrapped, 'Session.request',
                                       (request_method, url), kwargs)

        self.assertEqual(kwargs['headers']['key'], 'value')
        self.assertEqual(kwargs['headers']['x-trace'], 'some-value')

    def test_tracer_headers_are_overwritten(self):
        wrapped = mock.Mock(return_value=mock.Mock(status_code=200))
        mock_tracer = MockTracer(
            propagator=mock.Mock(
                to_headers=lambda x: {'x-trace': 'some-value'}))

        patch = mock.patch(
            'opencensus.ext.requests.trace.execution_context.'
            'get_opencensus_tracer',
            return_value=mock_tracer)

        patch_thread = mock.patch(
            'opencensus.ext.requests.trace.execution_context.'
            'is_exporter',
            return_value=False)

        url = 'http://localhost:8080'
        request_method = 'POST'
        kwargs = {'headers': {'x-trace': 'original-value'}}

        with patch, patch_thread:
            trace.wrap_session_request(wrapped, 'Session.request',
                                       (request_method, url), kwargs)

        self.assertEqual(kwargs['headers']['x-trace'], 'some-value')

    def test_wrap_session_request_timeout(self):
        wrapped = mock.Mock(return_value=mock.Mock(status_code=200))
        wrapped.side_effect = requests.Timeout

        mock_tracer = MockTracer(
            propagator=mock.Mock(
                to_headers=lambda x: {'x-trace': 'some-value'}))

        patch = mock.patch(
            'opencensus.ext.requests.trace.execution_context.'
            'get_opencensus_tracer',
            return_value=mock_tracer)
        patch_thread = mock.patch(
            'opencensus.ext.requests.trace.execution_context.'
            'is_exporter',
            return_value=False)

        url = 'http://localhost:8080/test'
        request_method = 'POST'
        kwargs = {}

        with patch, patch_thread:
            trace.wrap_session_request(wrapped, 'Session.request',
                                       (request_method, url), kwargs)

        expected_attributes = {
            'http.host': 'localhost:8080',
            'http.method': 'POST',
            'http.path': '/test',
            'http.url': url,
        }
        expected_name = '/test'
        expected_status = status_module.Status(4, 'request timed out')

        self.assertEqual(span_module.SpanKind.CLIENT,
                         mock_tracer.current_span.span_kind)
        self.assertEqual(expected_attributes,
                         mock_tracer.current_span.attributes)
        self.assertEqual(kwargs['headers']['x-trace'], 'some-value')
        self.assertEqual(expected_name, mock_tracer.current_span.name)
        self.assertEqual(
            expected_status.__dict__,
            mock_tracer.current_span.status.__dict__
        )

    def test_wrap_session_request_invalid_url(self):
        wrapped = mock.Mock(return_value=mock.Mock(status_code=200))
        wrapped.side_effect = requests.URLRequired

        mock_tracer = MockTracer(
            propagator=mock.Mock(
                to_headers=lambda x: {'x-trace': 'some-value'}))

        patch = mock.patch(
            'opencensus.ext.requests.trace.execution_context.'
            'get_opencensus_tracer',
            return_value=mock_tracer)
        patch_thread = mock.patch(
            'opencensus.ext.requests.trace.execution_context.'
            'is_exporter',
            return_value=False)

        url = 'http://localhost:8080/test'
        request_method = 'POST'
        kwargs = {}

        with patch, patch_thread:
            trace.wrap_session_request(wrapped, 'Session.request',
                                       (request_method, url), kwargs)

        expected_attributes = {
            'http.host': 'localhost:8080',
            'http.method': 'POST',
            'http.path': '/test',
            'http.url': url,
        }
        expected_name = '/test'
        expected_status = status_module.Status(3, 'invalid URL')

        self.assertEqual(span_module.SpanKind.CLIENT,
                         mock_tracer.current_span.span_kind)
        self.assertEqual(expected_attributes,
                         mock_tracer.current_span.attributes)
        self.assertEqual(kwargs['headers']['x-trace'], 'some-value')
        self.assertEqual(expected_name, mock_tracer.current_span.name)
        self.assertEqual(
            expected_status.__dict__,
            mock_tracer.current_span.status.__dict__
        )

    def test_wrap_session_request_exception(self):
        wrapped = mock.Mock(return_value=mock.Mock(status_code=200))
        wrapped.side_effect = requests.TooManyRedirects

        mock_tracer = MockTracer(
            propagator=mock.Mock(
                to_headers=lambda x: {'x-trace': 'some-value'}))

        patch = mock.patch(
            'opencensus.ext.requests.trace.execution_context.'
            'get_opencensus_tracer',
            return_value=mock_tracer)
        patch_thread = mock.patch(
            'opencensus.ext.requests.trace.execution_context.'
            'is_exporter',
            return_value=False)

        url = 'http://localhost:8080/test'
        request_method = 'POST'
        kwargs = {}

        with patch, patch_thread:
            trace.wrap_session_request(wrapped, 'Session.request',
                                       (request_method, url), kwargs)

        expected_attributes = {
            'http.host': 'localhost:8080',
            'http.method': 'POST',
            'http.path': '/test',
            'http.url': url,
        }
        expected_name = '/test'
        expected_status = status_module.Status(2, '')

        self.assertEqual(span_module.SpanKind.CLIENT,
                         mock_tracer.current_span.span_kind)
        self.assertEqual(expected_attributes,
                         mock_tracer.current_span.attributes)
        self.assertEqual(kwargs['headers']['x-trace'], 'some-value')
        self.assertEqual(expected_name, mock_tracer.current_span.name)
        self.assertEqual(
            expected_status.__dict__,
            mock_tracer.current_span.status.__dict__
        )


class MockTracer(object):
    def __init__(self, propagator=None):
        self.current_span = None
        self.span_context = {}
        self.propagator = propagator

    def start_span(self):
        span = MockSpan()
        self.current_span = span
        return span

    def end_span(self):
        pass

    def add_attribute_to_current_span(self, key, value):
        self.current_span.attributes[key] = value


class MockSpan(object):
    def __init__(self):
        self.attributes = {}

    def set_status(self, status):
        self.status = status
