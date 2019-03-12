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

import mock
from pyramid.registry import Registry
from pyramid.response import Response
from pyramid.testing import DummyRequest

from opencensus.common.transports import sync
from opencensus.ext.pyramid import pyramid_middleware
from opencensus.ext.zipkin import trace_exporter as zipkin_exporter
from opencensus.trace import execution_context
from opencensus.trace import print_exporter
from opencensus.trace import span as span_module
from opencensus.trace.propagation import google_cloud_format
from opencensus.trace.samplers import always_on
from opencensus.trace.blank_span import BlankSpan
from opencensus.trace.tracers import noop_tracer


class TestPyramidMiddleware(unittest.TestCase):
    def tearDown(self):
        from opencensus.trace import execution_context

        execution_context.clear()

    def test_constructor(self):
        pyramid_trace_header = 'X-Cloud-Trace-Context'
        trace_id = '2dd43a1d6b2549c6bc2a1a54c2fc0b05'
        span_id = '6e0c63257de34c92'
        pyramid_trace_id = '{}/{}'.format(trace_id, span_id)

        response = Response()

        def dummy_handler(request):
            return response

        mock_registry = mock.Mock(spec=Registry)
        mock_registry.settings = {}
        mock_registry.settings['OPENCENSUS_TRACE'] = {
            'EXPORTER': print_exporter.PrintExporter()}

        middleware = pyramid_middleware.OpenCensusTweenFactory(
            dummy_handler,
            mock_registry,
        )

        assert isinstance(middleware.sampler, always_on.AlwaysOnSampler)
        assert isinstance(
            middleware.exporter, print_exporter.PrintExporter)
        assert isinstance(
            middleware.propagator,
            google_cloud_format.GoogleCloudFormatPropagator)

        # Just a smoke test to make sure things work
        request = DummyRequest(
            registry=mock_registry,
            path='/',
            headers={pyramid_trace_header: pyramid_trace_id},
        )

        assert middleware(request) == response

    def test_constructor_zipkin(self):
        service_name = 'test_service'
        host_name = 'test_hostname'
        port = 2333

        response = Response()

        def dummy_handler(request):
            return response

        exporter = zipkin_exporter.ZipkinExporter(
            service_name=service_name,
            host_name=host_name,
            port=port,
            transport=sync.SyncTransport
        )

        mock_registry = mock.Mock(spec=Registry)
        mock_registry.settings = {}
        mock_registry.settings['OPENCENSUS_TRACE'] = {
            'EXPORTER': exporter,
        }

        middleware = pyramid_middleware.OpenCensusTweenFactory(
            dummy_handler,
            mock_registry,
        )

        assert isinstance(middleware.sampler, always_on.AlwaysOnSampler)
        assert isinstance(
            middleware.exporter, zipkin_exporter.ZipkinExporter)
        assert isinstance(
            middleware.propagator,
            google_cloud_format.GoogleCloudFormatPropagator)

        self.assertEqual(middleware.exporter.service_name, service_name)
        self.assertEqual(middleware.exporter.host_name, host_name)
        self.assertEqual(middleware.exporter.port, port)

    def test__before_request(self):
        pyramid_trace_header = 'X-Cloud-Trace-Context'
        trace_id = '2dd43a1d6b2549c6bc2a1a54c2fc0b05'
        span_id = '6e0c63257de34c92'
        pyramid_trace_id = '{}/{}'.format(trace_id, span_id)

        response = Response()

        def dummy_handler(request):
            return response

        mock_registry = mock.Mock(spec=Registry)
        mock_registry.settings = {}

        middleware = pyramid_middleware.OpenCensusTweenFactory(
            dummy_handler,
            mock_registry,
        )

        request = DummyRequest(
            registry=mock_registry,
            path='/',
            headers={pyramid_trace_header: pyramid_trace_id},
        )

        middleware._before_request(request)
        tracer = execution_context.get_opencensus_tracer()
        self.assertIsNotNone(tracer)

        span = tracer.current_span()

        expected_attributes = {
            'http.url': u'/',
            'http.method': 'GET',
        }

        self.assertEqual(span.span_kind, span_module.SpanKind.SERVER)
        self.assertEqual(span.attributes, expected_attributes)
        self.assertEqual(span.parent_span.span_id, span_id)

        span_context = tracer.span_context
        self.assertEqual(span_context.trace_id, trace_id)

    def test__before_request_blacklist(self):
        pyramid_trace_header = 'X-Cloud-Trace-Context'
        trace_id = '2dd43a1d6b2549c6bc2a1a54c2fc0b05'
        span_id = '6e0c63257de34c92'
        pyramid_trace_id = '{}/{}'.format(trace_id, span_id)

        response = Response()

        def dummy_handler(request):
            return response

        mock_registry = mock.Mock(spec=Registry)
        mock_registry.settings = {}

        middleware = pyramid_middleware.OpenCensusTweenFactory(
            dummy_handler,
            mock_registry,
        )

        request = DummyRequest(
            registry=mock_registry,
            path='/_ah/health',
            headers={pyramid_trace_header: pyramid_trace_id},
        )

        middleware._before_request(request)

        tracer = execution_context.get_opencensus_tracer()
        assert isinstance(tracer, noop_tracer.NoopTracer)

        span = tracer.current_span()

        assert isinstance(span, BlankSpan)

    def test__after_request(self):
        pyramid_trace_header = 'X-Cloud-Trace-Context'
        trace_id = '2dd43a1d6b2549c6bc2a1a54c2fc0b05'
        span_id = '6e0c63257de34c92'
        pyramid_trace_id = '{}/{}'.format(trace_id, span_id)

        response = Response(status=200)

        def dummy_handler(request):
            return response

        mock_registry = mock.Mock(spec=Registry)
        mock_registry.settings = {}

        middleware = pyramid_middleware.OpenCensusTweenFactory(
            dummy_handler,
            mock_registry,
        )

        request = DummyRequest(
            registry=mock_registry,
            path='/',
            headers={pyramid_trace_header: pyramid_trace_id},
        )

        middleware._before_request(request)

        tracer = execution_context.get_opencensus_tracer()
        self.assertIsNotNone(tracer)

        span = tracer.current_span()

        expected_attributes = {
            'http.url': u'/',
            'http.method': 'GET',
            'http.status_code': '200',
        }

        self.assertEqual(span.parent_span.span_id, span_id)

        middleware._after_request(request, response)

        self.assertEqual(span.attributes, expected_attributes)

    def test__after_request_blacklist(self):
        pyramid_trace_header = 'X-Cloud-Trace-Context'
        trace_id = '2dd43a1d6b2549c6bc2a1a54c2fc0b05'
        span_id = '6e0c63257de34c92'
        pyramid_trace_id = '{}/{}'.format(trace_id, span_id)

        response = Response()

        def dummy_handler(request):
            return response

        mock_registry = mock.Mock(spec=Registry)
        mock_registry.settings = {}

        middleware = pyramid_middleware.OpenCensusTweenFactory(
            dummy_handler,
            mock_registry,
        )

        request = DummyRequest(
            registry=mock_registry,
            path='/_ah/health',
            headers={pyramid_trace_header: pyramid_trace_id},
        )

        middleware._before_request(request)

        tracer = execution_context.get_opencensus_tracer()
        assert isinstance(tracer, noop_tracer.NoopTracer)

        span = tracer.current_span()

        middleware._after_request(request, response)

        assert isinstance(span, BlankSpan)
