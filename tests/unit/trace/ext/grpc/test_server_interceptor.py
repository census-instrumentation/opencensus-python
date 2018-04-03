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
from google.rpc import code_pb2

from opencensus.trace import execution_context
from opencensus.trace import span as span_module
from opencensus.trace.ext.grpc import server_interceptor


class TestOpenCensusServerInterceptor(unittest.TestCase):
    def test_constructor(self):
        sampler = mock.Mock()
        exporter = mock.Mock()
        interceptor = server_interceptor.OpenCensusServerInterceptor(
            sampler=sampler, exporter=exporter)
        self.assertEqual(interceptor.sampler, sampler)
        self.assertEqual(interceptor.exporter, exporter)

    def test_rpc_handler_wrapper(self):
        """Ensure that RPCHandlerWrapper proxies to the unerlying handler"""
        mock_handler = mock.Mock()
        mock_handler.response_streaming = False
        wrapper = server_interceptor.RpcMethodHandlerWrapper(mock_handler)
        self.assertEqual(wrapper.response_streaming, False)

    def test_intercept_handler_no_metadata(self):
        patch = mock.patch(
            'opencensus.trace.ext.grpc.server_interceptor.tracer_module.Tracer',
            MockTracer)
        mock_context = mock.Mock()
        mock_context.invocation_metadata = mock.Mock(return_value=None)
        interceptor = server_interceptor.OpenCensusServerInterceptor(
            None, None)

        with patch:
            interceptor.intercept_handler(
                mock.Mock(), mock.Mock()
            ).unary_unary(mock.Mock(), mock_context)

        expected_attributes = {
            '/component': 'grpc',
        }

        self.assertEqual(
            execution_context.get_opencensus_tracer().current_span().attributes,
            expected_attributes)

    def test_intercept_handler(self):
        patch = mock.patch(
            'opencensus.trace.ext.grpc.server_interceptor.tracer_module.Tracer',
            MockTracer)
        mock_context = mock.Mock()
        mock_context.invocation_metadata = mock.Mock(
            return_value=(('test_key', b'test_value'),)
        )
        interceptor = server_interceptor.OpenCensusServerInterceptor(
            None, None)

        with patch:
            interceptor.intercept_handler(
                mock.Mock(), mock.Mock()
            ).unary_unary(mock.Mock(), mock_context)

        expected_attributes = {
            '/component': 'grpc',
        }

        self.assertEqual(
            execution_context.get_opencensus_tracer().current_span().attributes,
            expected_attributes)

    def test_intercept_service(self):
        interceptor = server_interceptor.OpenCensusServerInterceptor(
            None, None)
        mock_handler = mock.Mock()
        interceptor.intercept_handler = mock_handler
        interceptor.intercept_service(None, None)
        self.assertTrue(mock_handler.called)

    def test_intercept_handler_exception(self):
        patch = mock.patch(
            'opencensus.trace.ext.grpc.server_interceptor.tracer_module.Tracer',
            MockTracer)
        interceptor = server_interceptor.OpenCensusServerInterceptor(
            None, None)
        mock_context = mock.Mock()
        mock_context.invocation_metadata = mock.Mock(return_value=None)
        mock_continuation = mock.Mock()
        mock_continuation.unary_unary = mock.Mock(side_effect=Exception('Test'))
        with patch:
            # patch the wrapper's handler to return an exception
            rpc_wrapper = interceptor.intercept_handler(
                mock.Mock(), mock.Mock())
            rpc_wrapper.handler.unary_unary = mock.Mock(
                side_effect=Exception('Test'))
            with self.assertRaises(Exception):
                rpc_wrapper.unary_unary(mock.Mock(), mock_context)

        expected_attributes = {
            '/component': 'grpc',
            '/error/message': 'Test'
        }

        current_span = execution_context.get_opencensus_tracer().current_span()
        self.assertEqual(
            execution_context.get_opencensus_tracer().current_span().attributes,
            expected_attributes)

        # check that the stack trace is attached to the current span
        self.assertIsNotNone(current_span.stack_trace)
        self.assertIsNotNone(current_span.stack_trace.stack_trace_hash_id)
        self.assertNotEqual(current_span.stack_trace.stack_frames, [])

        # check that the status obj is attached to the current span
        self.assertIsNotNone(current_span.status)
        self.assertEqual(current_span.status.code, code_pb2.UNKNOWN)
        self.assertEqual(current_span.status.message, 'Test')


class MockTracer(object):
    def __init__(self, *args, **kwargs):
        self._current_span = span_module.Span('mock_span')
        execution_context.set_opencensus_tracer(self)

    def start_span(self, name):
        self._current_span.name = name
        return self._current_span

    def end_span(self):
        return

    def add_attribute_to_current_span(self, attribute_key, attribute_value):
        self._current_span.attributes[attribute_key] = attribute_value

    def current_span(self):
        return self._current_span
