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

from opencensus.ext.grpc import server_interceptor
from opencensus.trace import execution_context
from opencensus.trace import span as span_module


class TestOpenCensusServerInterceptor(unittest.TestCase):
    def test_constructor(self):
        sampler = mock.Mock()
        exporter = mock.Mock()
        interceptor = server_interceptor.OpenCensusServerInterceptor(
            sampler=sampler, exporter=exporter)
        self.assertEqual(interceptor.sampler, sampler)
        self.assertEqual(interceptor.exporter, exporter)

    def test_intercept_service_no_metadata(self):
        patch = mock.patch(
            'opencensus.ext.grpc.server_interceptor'
            '.tracer_module.Tracer', MockTracer)
        mock_context = mock.Mock()
        mock_context.invocation_metadata = mock.Mock(return_value=None)
        mock_context._rpc_event.call_details.method = 'hello'
        interceptor = server_interceptor.OpenCensusServerInterceptor(
            None, None)
        mock_handler = mock.Mock()
        mock_handler.request_streaming = False
        mock_handler.response_streaming = False
        mock_continuation = mock.Mock(return_value=mock_handler)

        with patch:
            interceptor.intercept_service(mock_continuation,
                                          mock.Mock()).unary_unary(
                                              mock.Mock(), mock_context)

        expected_attributes = {
            'component': 'grpc',
        }

        self.assertEqual(
            execution_context.get_opencensus_tracer().current_span().
            attributes, expected_attributes)

    def test_intercept_service(self):
        test_dimensions = [
            ['unary_unary', False, False],
            ['unary_stream', False, True],
            ['stream_unary', True, False],
            ['stream_stream', True, True],
        ]
        for rpc_fn_name, req_streaming, rsp_streaming in test_dimensions:
            patch = mock.patch(
                'opencensus.ext.grpc.server_interceptor.tracer_module'
                '.Tracer', MockTracer)
            mock_context = mock.Mock()
            mock_context.invocation_metadata = mock.Mock(
                return_value=(('test_key', b'test_value'), ))
            mock_handler = mock.Mock()
            mock_handler.request_streaming = req_streaming
            mock_handler.response_streaming = rsp_streaming
            mock_continuation = mock.Mock(return_value=mock_handler)

            mock_context._rpc_event.call_details.method = 'hello'
            interceptor = server_interceptor.OpenCensusServerInterceptor(
                None, None)

            with patch:
                handler = interceptor.intercept_service(
                    mock_continuation, mock.Mock())
                getattr(handler, rpc_fn_name)(mock.Mock(), mock_context)

            expected_attributes = {
                'component': 'grpc',
            }

            self.assertEqual(
                execution_context.get_opencensus_tracer().current_span().
                attributes, expected_attributes)

    def test_intercept_handler_exception(self):
        test_dimensions = [
            ['unary_unary', False, False],
            ['unary_stream', False, True],
            ['stream_unary', True, False],
            ['stream_stream', True, True],
        ]
        for rpc_fn_name, req_streaming, rsp_streaming in test_dimensions:
            patch = mock.patch(
                'opencensus.ext.grpc.server_interceptor'
                '.tracer_module.Tracer', MockTracer)
            interceptor = server_interceptor.OpenCensusServerInterceptor(
                None, None)
            mock_context = mock.Mock()
            mock_context.invocation_metadata = mock.Mock(return_value=None)
            mock_context._rpc_event.call_details.method = 'hello'
            mock_handler = mock.Mock()
            mock_handler.request_streaming = req_streaming
            mock_handler.response_streaming = rsp_streaming
            setattr(mock_handler, rpc_fn_name,
                    mock.Mock(side_effect=Exception('Test')))
            mock_continuation = mock.Mock(return_value=mock_handler)

            # mock_continuation.unary_unary = mock.Mock())
            with patch:
                # patch the wrapper's handler to return an exception
                handler = interceptor.intercept_service(
                    mock_continuation, mock.Mock())
                with self.assertRaises(Exception):
                    getattr(handler, rpc_fn_name)(mock.Mock(), mock_context)

            expected_attributes = {
                'component': 'grpc',
                'error.message': 'Test'
            }

            current_span = execution_context.get_opencensus_tracer(
            ).current_span()
            self.assertEqual(
                execution_context.get_opencensus_tracer().current_span().
                attributes, expected_attributes)

            self.assertEqual(current_span.span_kind,
                             span_module.SpanKind.SERVER)

            # check that the stack trace is attached to the current span
            self.assertIsNotNone(current_span.stack_trace)
            self.assertIsNotNone(current_span.stack_trace.stack_trace_hash_id)
            self.assertNotEqual(current_span.stack_trace.stack_frames, [])

            # check that the status obj is attached to the current span
            self.assertIsNotNone(current_span.status)
            self.assertEqual(current_span.status.code, code_pb2.UNKNOWN)
            self.assertEqual(current_span.status.message, 'Test')

    def test__wrap_rpc_behavior_none(self):
        new_handler = server_interceptor._wrap_rpc_behavior(None, lambda: None)
        self.assertEqual(new_handler, None)


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
