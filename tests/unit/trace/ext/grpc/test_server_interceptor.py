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

from opencensus.trace.ext.grpc import server_interceptor
from opencensus.trace import execution_context


class TestOpenCensusServerInterceptor(unittest.TestCase):
    def test_constructor(self):
        sampler = mock.Mock()
        exporter = mock.Mock()
        interceptor = server_interceptor.OpenCensusServerInterceptor(
            sampler=sampler, exporter=exporter)
        self.assertEqual(interceptor.sampler, sampler)
        self.assertEqual(interceptor.exporter, exporter)

    def test_intercept_handler_no_metadata(self):
        current_span = mock.Mock()
        mock_tracer = MockTracer(None, None, None)
        patch = mock.patch(
            'opencensus.trace.ext.grpc.server_interceptor.tracer_module.Tracer',
            MockTracer)
        mock_context = mock.Mock()
        mock_context.invocation_metadata = mock.Mock(return_value=None)
        interceptor = server_interceptor.OpenCensusServerInterceptor(
            None, None)

        with patch:
            interceptor.intercept_handler(mock.Mock(), mock.Mock()).unary_unary(mock.Mock(), mock_context)

        expected_attributes = {
            '/component': 'grpc',
        }

        self.assertEqual(
            execution_context.get_opencensus_tracer().current_span.attributes,
            expected_attributes)

    def test_intercept_handler(self):
        current_span = mock.Mock()
        mock_tracer = MockTracer(None, None, None)
        patch = mock.patch(
            'opencensus.trace.ext.grpc.server_interceptor.tracer_module.Tracer',
            MockTracer)
        mock_context = mock.Mock()
        mock_context.invocation_metadata = mock.Mock(return_value=(('test_key', b'test_value'),))
        interceptor = server_interceptor.OpenCensusServerInterceptor(
            None, None)

        with patch:
            interceptor.intercept_handler(mock.Mock(), mock.Mock()).unary_unary(mock.Mock(), mock_context)

        expected_attributes = {
            '/component': 'grpc',
        }

        self.assertEqual(
            execution_context.get_opencensus_tracer().current_span.attributes,
            expected_attributes)

    def test_intercept_service(self):
        interceptor = server_interceptor.OpenCensusServerInterceptor(
            None, None)
        mock_handler = mock.Mock()
        interceptor.intercept_handler = mock_handler
        interceptor.intercept_service(None, None)
        self.assertTrue(mock_handler.called)


class MockTracer(object):
    def __init__(self, *args, **kwargs):
        self.current_span = mock.Mock()
        self.current_span.attributes = {}
        execution_context.set_opencensus_tracer(self)

    def start_span(self, name):
        self.current_span.name = name
        span = mock.Mock()
        span.__enter__ = mock.Mock()
        span.__exit__ = mock.Mock()
        return span

    def end_span(self):
        return

    def add_attribute_to_current_span(self, attribute_key, attribute_value):
        self.current_span.attributes[attribute_key] = attribute_value
