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

from opencensus.ext.grpc import client_interceptor
from opencensus.trace import execution_context
from opencensus.trace.tracers.noop_tracer import NoopTracer


class TestOpenCensusClientInterceptor(unittest.TestCase):
    def setUp(self):
        execution_context.clear()

    def test_constructor_default(self):
        from opencensus.trace.propagation import binary_format

        interceptor = client_interceptor.OpenCensusClientInterceptor()

        self.assertIsNone(interceptor._tracer)
        self.assertIsNone(interceptor.host_port)
        self.assertTrue(
            isinstance(interceptor._propagator,
                       binary_format.BinaryFormatPropagator))

    def test_constructor_explicit(self):
        from opencensus.trace.propagation import binary_format

        tracer = mock.Mock()
        host_port = 'localhost:50051'
        interceptor = client_interceptor.OpenCensusClientInterceptor(
            tracer=tracer, host_port=host_port)

        self.assertEqual(interceptor._tracer, tracer)
        self.assertEqual(interceptor.host_port, host_port)
        self.assertTrue(
            isinstance(interceptor._propagator,
                       binary_format.BinaryFormatPropagator))

    def test__start_client_span(self):
        tracer = mock.Mock()
        interceptor = client_interceptor.OpenCensusClientInterceptor(
            tracer=tracer, host_port='test')
        mock_client_call_details = mock.Mock()
        mock_client_call_details.method = '/hello'
        interceptor._start_client_span(mock_client_call_details)

        self.assertTrue(tracer.start_span.called)
        self.assertTrue(tracer.add_attribute_to_current_span.called)

    def test__intercept_call_metadata_none(self):
        tracer = mock.Mock()
        tracer.span_context = mock.Mock()
        test_header = 'test header'
        mock_propagator = mock.Mock()
        mock_propagator.to_header.return_value = test_header

        interceptor = client_interceptor.OpenCensusClientInterceptor(
            tracer=tracer, host_port='test')
        interceptor._propagator = mock_propagator
        mock_client_call_details = mock.Mock()
        mock_client_call_details.metadata = None
        mock_client_call_details.method = '/hello'

        client_call_details, request_iterator, current_span =\
            interceptor._intercept_call(
                mock_client_call_details, mock.Mock(), 'unary_unary')

        expected_metadata = (('grpc-trace-bin', test_header), )

        self.assertEqual(expected_metadata, client_call_details.metadata)

    def test__intercept_call_noop_tracer(self):
        tracer = NoopTracer()
        test_header = 'test header'
        mock_propagator = mock.Mock()
        mock_propagator.to_header.return_value = test_header

        interceptor = client_interceptor.OpenCensusClientInterceptor(
            tracer=tracer, host_port='test')
        interceptor._propagator = mock_propagator
        mock_client_call_details = mock.Mock()
        mock_client_call_details.metadata = None
        mock_client_call_details.method = '/hello'

        client_call_details, request_iterator, current_span =\
            interceptor._intercept_call(
                mock_client_call_details, mock.Mock(), 'unary_unary')

        expected_metadata = (('grpc-trace-bin', test_header), )

        self.assertEqual(expected_metadata, client_call_details.metadata)

    def test__intercept_call_metadata_list(self):
        tracer = mock.Mock()
        tracer.span_context = mock.Mock()
        test_header = 'test header'
        mock_propagator = mock.Mock()
        mock_propagator.to_header.return_value = test_header

        interceptor = client_interceptor.OpenCensusClientInterceptor(
            tracer=tracer, host_port='test')
        interceptor._propagator = mock_propagator
        mock_client_call_details = mock.Mock()
        mock_client_call_details.metadata = [
            ('test_key', 'test_value'),
        ]
        mock_client_call_details.method = '/hello'

        client_call_details, request_iterator, current_span =\
            interceptor._intercept_call(
                mock_client_call_details, mock.Mock(), 'unary_unary')

        expected_metadata = [
            ('test_key', 'test_value'),
            ('grpc-trace-bin', test_header),
        ]

        self.assertEqual(expected_metadata, client_call_details.metadata)

    def test__intercept_call_metadata_tuple(self):
        tracer = mock.Mock()
        tracer.span_context = mock.Mock()
        test_header = 'test header'
        mock_propagator = mock.Mock()
        mock_propagator.to_header.return_value = test_header

        interceptor = client_interceptor.OpenCensusClientInterceptor(
            tracer=tracer, host_port='test')
        interceptor._propagator = mock_propagator
        mock_client_call_details = mock.Mock()
        mock_client_call_details.metadata = (('test_key', 'test_value'), )
        mock_client_call_details.method = '/hello'

        client_call_details, request_iterator, current_span =\
            interceptor._intercept_call(
                mock_client_call_details, mock.Mock(), 'unary_unary')

        expected_metadata = (
            ('test_key', 'test_value'),
            ('grpc-trace-bin', test_header),
        )

        self.assertEqual(expected_metadata, client_call_details.metadata)

    def test__callback(self):
        current_span = mock.Mock()
        tracer = MockTracer(current_span)
        interceptor = client_interceptor.OpenCensusClientInterceptor(
            tracer=tracer, host_port='test')
        current_span.attributes = {}
        callback = interceptor._callback(current_span)
        response = mock.Mock()
        response.exception.return_value = 'test_exception'
        callback(response)
        expected_attributes = {
            'error.message': 'test_exception',
        }

        self.assertEqual(current_span.attributes, expected_attributes)

    def test__callback_no_exception(self):
        current_span = mock.Mock()
        tracer = MockTracer(current_span)
        interceptor = client_interceptor.OpenCensusClientInterceptor(
            tracer=tracer, host_port='test')
        current_span.attributes = {}
        callback = interceptor._callback(current_span)
        response = mock.Mock()
        response.exception.return_value = None
        callback(response)
        expected_attributes = {'error.message': None}

        self.assertEqual(current_span.attributes, expected_attributes)

    def _unary_helper(self):
        continuation = mock.Mock()
        mock_response = mock.Mock()
        continuation.return_value = mock_response
        interceptor = client_interceptor.OpenCensusClientInterceptor()
        interceptor._intercept_call = mock.Mock(
            return_value=(None, iter([mock.Mock()]), None))
        return interceptor, continuation, mock_response

    def _stream_helper(self):
        continuation = mock.Mock()
        mock_response = iter([mock.Mock()])
        continuation.return_value = mock_response
        mock_tracer = mock.Mock()
        interceptor = client_interceptor.OpenCensusClientInterceptor(
            tracer=mock_tracer)
        interceptor._intercept_call = mock.Mock(
            return_value=(None, iter([mock.Mock()]), mock.Mock()))
        return interceptor, continuation, mock_tracer

    def test_intercept_unary_unary_trace(self):
        interceptor, continuation, mock_response = self._unary_helper()
        client_call_details = mock.Mock()
        client_call_details.method = 'test'
        interceptor.intercept_unary_unary(continuation, client_call_details,
                                          [])
        self.assertTrue(mock_response.add_done_callback.called)

    def test_intercept_unary_unary_not_trace(self):
        interceptor, continuation, mock_response = self._unary_helper()
        client_call_details = mock.Mock()
        client_call_details.method = 'google.devtools.cloudtrace'
        interceptor.intercept_unary_unary(continuation, client_call_details,
                                          [])
        # Should skip tracing the cloud trace activities
        self.assertFalse(mock_response.add_done_callback.called)

    def test_intercept_unary_stream_trace(self):
        interceptor, continuation, mock_tracer = self._stream_helper()
        execution_context.set_opencensus_tracer(mock_tracer)
        client_call_details = mock.Mock()
        client_call_details.method = 'test'
        response_iter = interceptor.intercept_unary_stream(
            continuation, client_call_details, [])
        for _ in response_iter:
            pass
        self.assertTrue(mock_tracer.end_span.called)

    def test_intercept_unary_stream_not_trace(self):
        interceptor, continuation, mock_tracer = self._stream_helper()
        client_call_details = mock.Mock()
        client_call_details.method = 'google.devtools.cloudtrace'
        interceptor.intercept_unary_stream(continuation, client_call_details,
                                           [])
        # Should skip tracing the cloud trace activities
        self.assertFalse(mock_tracer.end_span.called)

    def test_intercept_stream_unary_trace(self):
        interceptor, continuation, mock_response = self._unary_helper()
        client_call_details = mock.Mock()
        client_call_details.method = 'test'
        interceptor.intercept_stream_unary(continuation, client_call_details,
                                           [])
        self.assertTrue(mock_response.add_done_callback.called)

    def test_intercept_stream_unary_not_trace(self):
        interceptor, continuation, mock_tracer = self._stream_helper()
        client_call_details = mock.Mock()
        client_call_details.method = 'google.devtools.cloudtrace'
        interceptor.intercept_stream_unary(continuation, client_call_details,
                                           [])
        # Should skip tracing the cloud trace activities
        self.assertFalse(mock_tracer.end_span.called)

    def test_intercept_stream_stream_trace(self):
        interceptor, continuation, mock_tracer = self._stream_helper()
        execution_context.set_opencensus_tracer(mock_tracer)
        client_call_details = mock.Mock()
        client_call_details.method = 'test'
        response_iter = interceptor.intercept_stream_stream(
            continuation, client_call_details, [])
        for _ in response_iter:
            pass

        self.assertTrue(mock_tracer.end_span.called)

    def test_intercept_stream_stream_not_trace(self):
        interceptor, continuation, mock_tracer = self._stream_helper()
        client_call_details = mock.Mock()
        client_call_details.method = 'google.devtools.cloudtrace'
        interceptor.intercept_stream_stream(continuation, client_call_details,
                                            [])
        # Should skip tracing the cloud trace activities
        self.assertFalse(mock_tracer.end_span.called)


class MockTracer(object):
    def __init__(self, current_span):
        self.current_span = current_span

    def add_attribute_to_current_span(self, attribute_key, attribute_value):
        self.current_span.attributes[attribute_key] = attribute_value

    def end_span(self):
        return
