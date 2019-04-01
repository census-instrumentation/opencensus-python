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
from django.test import RequestFactory
from django.test.utils import teardown_test_environment

from opencensus.common.transports import sync
from opencensus.ext.jaeger import trace_exporter as jaeger_exporter
from opencensus.ext.ocagent import trace_exporter as ocagent_exporter
from opencensus.ext.zipkin import trace_exporter as zipkin_exporter
from opencensus.trace import execution_context
from opencensus.trace import print_exporter
from opencensus.trace import span as span_module
from opencensus.trace import utils
from opencensus.trace.propagation import google_cloud_format
from opencensus.trace.samplers import always_on
from opencensus.trace.samplers import probability
from opencensus.trace.blank_span import BlankSpan


class TestOpencensusMiddleware(unittest.TestCase):

    def setUp(self):
        from django.conf import settings as django_settings
        from django.test.utils import setup_test_environment

        if not django_settings.configured:
            django_settings.configure()
        setup_test_environment()

    def tearDown(self):
        execution_context.clear()
        teardown_test_environment()

    def test_constructor_cloud(self):
        from opencensus.ext.django import middleware

        class MockCloudExporter(object):
            def __init__(self, project_id, transport):
                self.project_id = project_id
                self.transport = transport

        MockCloudExporter.__name__ = 'GoogleCloudExporter'

        project_id = 'my_project'
        params = {
            'GCP_EXPORTER_PROJECT': project_id,
            'TRANSPORT':
                'opencensus.common.transports.sync.SyncTransport',
        }

        patch_params = mock.patch(
            'opencensus.ext.django.config.settings.params', params)
        patch_exporter = mock.patch(
            'opencensus.ext.django.config.settings.EXPORTER',
            MockCloudExporter)

        with patch_params, patch_exporter:
            middleware = middleware.OpencensusMiddleware()

        self.assertIs(middleware._sampler, always_on.AlwaysOnSampler)
        self.assertIs(
            middleware._exporter, MockCloudExporter)
        self.assertIs(
            middleware._propagator,
            google_cloud_format.GoogleCloudFormatPropagator)

        assert isinstance(middleware.sampler, always_on.AlwaysOnSampler)
        assert isinstance(
            middleware.exporter, MockCloudExporter)
        assert isinstance(
            middleware.propagator,
            google_cloud_format.GoogleCloudFormatPropagator)

        self.assertEqual(middleware.exporter.project_id, project_id)
        self.assertEqual(middleware.exporter.transport, sync.SyncTransport)

    def test_constructor_zipkin(self):
        from opencensus.ext.django import middleware

        service_name = 'test_service'
        host_name = 'test_hostname'
        port = 2333
        protocol = 'http'
        params = {
            'ZIPKIN_EXPORTER_SERVICE_NAME': service_name,
            'ZIPKIN_EXPORTER_HOST_NAME': host_name,
            'ZIPKIN_EXPORTER_PORT': port,
            'ZIPKIN_EXPORTER_PROTOCOL': protocol,
            'TRANSPORT':
                'opencensus.common.transports.sync.SyncTransport',
        }

        patch_zipkin = mock.patch(
            'opencensus.ext.django.config.settings.EXPORTER',
            zipkin_exporter.ZipkinExporter)

        patch_params = mock.patch(
            'opencensus.ext.django.config.settings.params',
            params)

        with patch_zipkin, patch_params:
            middleware = middleware.OpencensusMiddleware()

        self.assertIs(middleware._sampler, always_on.AlwaysOnSampler)
        self.assertIs(
            middleware._exporter, zipkin_exporter.ZipkinExporter)
        self.assertIs(
            middleware._propagator,
            google_cloud_format.GoogleCloudFormatPropagator)

        assert isinstance(middleware.sampler, always_on.AlwaysOnSampler)
        assert isinstance(
            middleware.exporter, zipkin_exporter.ZipkinExporter)
        assert isinstance(
            middleware.propagator,
            google_cloud_format.GoogleCloudFormatPropagator)

        self.assertEqual(middleware.exporter.service_name, service_name)
        self.assertEqual(middleware.exporter.host_name, host_name)
        self.assertEqual(middleware.exporter.port, port)

    def test_constructor_jaeger(self):
        from opencensus.ext.django import middleware

        service_name = 'test_service'
        params = {
            'SERVICE_NAME': service_name,
            'TRANSPORT':
                'opencensus.common.transports.sync.SyncTransport',
        }

        patch_jaeger = mock.patch(
            'opencensus.ext.django.config.settings.EXPORTER',
            jaeger_exporter.JaegerExporter)

        patch_params = mock.patch(
            'opencensus.ext.django.config.settings.params',
            params)

        with patch_jaeger, patch_params:
            middleware = middleware.OpencensusMiddleware()

        self.assertIs(middleware._sampler, always_on.AlwaysOnSampler)
        self.assertIs(
            middleware._exporter, jaeger_exporter.JaegerExporter)
        self.assertIs(
            middleware._propagator,
            google_cloud_format.GoogleCloudFormatPropagator)

        assert isinstance(middleware.sampler, always_on.AlwaysOnSampler)
        assert isinstance(
            middleware.exporter, jaeger_exporter.JaegerExporter)
        assert isinstance(
            middleware.propagator,
            google_cloud_format.GoogleCloudFormatPropagator)

        self.assertEqual(middleware.exporter.service_name, service_name)

    def test_constructor_zipkin_service_name_param(self):
        from opencensus.ext.django import middleware

        service_name = 'test_service'
        host_name = 'test_hostname'
        port = 2333
        protocol = 'http'
        params = {
            'SERVICE_NAME': service_name,
            'ZIPKIN_EXPORTER_HOST_NAME': host_name,
            'ZIPKIN_EXPORTER_PORT': port,
            'ZIPKIN_EXPORTER_PROTOCOL': protocol,
            'TRANSPORT':
                'opencensus.common.transports.sync.SyncTransport',
        }

        patch_zipkin = mock.patch(
            'opencensus.ext.django.config.settings.EXPORTER',
            zipkin_exporter.ZipkinExporter)

        patch_params = mock.patch(
            'opencensus.ext.django.config.settings.params',
            params)

        with patch_zipkin, patch_params:
            middleware = middleware.OpencensusMiddleware()

        self.assertEqual(middleware.exporter.service_name, service_name)
        self.assertEqual(middleware.exporter.host_name, host_name)
        self.assertEqual(middleware.exporter.port, port)

    def test_constructor_ocagent_trace_exporter(self):
        from opencensus.ext.django import middleware

        service_name = 'test_service'
        endpoint = 'localhost:50001'
        params = {
            'SERVICE_NAME': service_name,
            'OCAGENT_TRACE_EXPORTER_ENDPOINT': endpoint,
            'TRANSPORT':
                'opencensus.common.transports.sync.SyncTransport',
        }

        patch_ocagent_trace = mock.patch(
            'opencensus.ext.django.config.settings.EXPORTER',
            ocagent_exporter.TraceExporter)

        patch_params = mock.patch(
            'opencensus.ext.django.config.settings.params',
            params)

        with patch_ocagent_trace, patch_params:
            middleware = middleware.OpencensusMiddleware()

        self.assertIs(middleware._sampler, always_on.AlwaysOnSampler)
        self.assertIs(
            middleware._exporter, ocagent_exporter.TraceExporter)
        self.assertIs(
            middleware._propagator,
            google_cloud_format.GoogleCloudFormatPropagator)

        assert isinstance(middleware.sampler, always_on.AlwaysOnSampler)
        assert isinstance(
            middleware.exporter, ocagent_exporter.TraceExporter)
        assert isinstance(
            middleware.propagator,
            google_cloud_format.GoogleCloudFormatPropagator)

        self.assertEqual(middleware.exporter.service_name, service_name)
        self.assertEqual(middleware.exporter.endpoint, endpoint)

    def test_constructor_ocagent_trace_exporter_default_endpoint(self):
        from opencensus.ext.django import middleware

        service_name = 'test_service'
        params = {
            'SERVICE_NAME': service_name,
            'TRANSPORT':
                'opencensus.common.transports.sync.SyncTransport',
        }

        patch_ocagent_trace = mock.patch(
            'opencensus.ext.django.config.settings.EXPORTER',
            ocagent_exporter.TraceExporter)

        patch_params = mock.patch(
            'opencensus.ext.django.config.settings.params',
            params)

        with patch_ocagent_trace, patch_params:
            middleware = middleware.OpencensusMiddleware()

        self.assertEqual(middleware.exporter.service_name, service_name)
        self.assertEqual(middleware.exporter.endpoint,
                         ocagent_exporter.DEFAULT_ENDPOINT)

    def test_constructor_probability_sampler(self):
        from opencensus.ext.django import middleware

        rate = 0.8
        params = {
            'SAMPLING_RATE': 0.8,
            'TRANSPORT':
                'opencensus.common.transports.sync.SyncTransport',
        }

        patch_sampler = mock.patch(
            'opencensus.ext.django.config.settings.SAMPLER',
            probability.ProbabilitySampler)
        patch_exporter = mock.patch(
            'opencensus.ext.django.config.settings.EXPORTER',
            print_exporter.PrintExporter)

        patch_params = mock.patch(
            'opencensus.ext.django.config.settings.params',
            params)

        with patch_sampler, patch_exporter, patch_params:
            middleware = middleware.OpencensusMiddleware()

        self.assertIs(middleware._sampler, probability.ProbabilitySampler)
        self.assertIs(
            middleware._exporter, print_exporter.PrintExporter)
        self.assertIs(
            middleware._propagator,
            google_cloud_format.GoogleCloudFormatPropagator)

        assert isinstance(middleware.sampler, probability.ProbabilitySampler)
        assert isinstance(
            middleware.exporter, print_exporter.PrintExporter)
        assert isinstance(
            middleware.propagator,
            google_cloud_format.GoogleCloudFormatPropagator)

        self.assertEqual(middleware.sampler.rate, rate)

    def test_process_request(self):
        from opencensus.ext.django import middleware

        trace_id = '2dd43a1d6b2549c6bc2a1a54c2fc0b05'
        span_id = '6e0c63257de34c92'
        django_trace_id = '{}/{}'.format(trace_id, span_id)

        django_request = RequestFactory().get('/', **{
            'HTTP_X_CLOUD_TRACE_CONTEXT': django_trace_id})

        middleware_obj = middleware.OpencensusMiddleware()

        # test process_request
        middleware_obj.process_request(django_request)

        tracer = middleware._get_current_tracer()

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

        # test process_view
        view_func = mock.Mock()
        middleware_obj.process_view(django_request, view_func)

        self.assertEqual(span.name, 'mock.mock.Mock')

    def test_blacklist_path(self):
        from opencensus.ext.django import middleware

        execution_context.clear()

        blacklist_paths = ['test_blacklist_path', ]
        params = {
            'BLACKLIST_PATHS': ['test_blacklist_path', ],
            'TRANSPORT':
                'opencensus.common.transports.sync.SyncTransport', }
        patch_params = mock.patch(
            'opencensus.ext.django.middleware.settings.params',
            params)

        with patch_params:
            middleware_obj = middleware.OpencensusMiddleware()

        django_request = RequestFactory().get('/test_blacklist_path')
        disabled = utils.disable_tracing_url(django_request.path,
                                             blacklist_paths)
        self.assertTrue(disabled)
        self.assertEqual(middleware_obj._blacklist_paths, blacklist_paths)

        # test process_request
        middleware_obj.process_request(django_request)

        tracer = middleware._get_current_tracer()
        span = tracer.current_span()

        # process view
        view_func = mock.Mock()
        middleware_obj.process_view(django_request, view_func)

        tracer = middleware._get_current_tracer()
        span = tracer.current_span()

        assert isinstance(span, BlankSpan)

        # process response
        django_response = mock.Mock()
        django_response.status_code = 200

        middleware_obj.process_response(django_request, django_response)

        tracer = middleware._get_current_tracer()
        span = tracer.current_span()
        assert isinstance(span, BlankSpan)

    def test_process_response(self):
        from opencensus.ext.django import middleware

        trace_id = '2dd43a1d6b2549c6bc2a1a54c2fc0b05'
        span_id = '6e0c63257de34c92'
        django_trace_id = '{}/{}'.format(trace_id, span_id)

        django_request = RequestFactory().get('/', **{
            google_cloud_format._TRACE_CONTEXT_HEADER_NAME: django_trace_id})

        middleware_obj = middleware.OpencensusMiddleware()

        middleware_obj.process_request(django_request)
        tracer = middleware._get_current_tracer()
        span = tracer.current_span()

        exporter_mock = mock.Mock()
        tracer.exporter = exporter_mock

        django_response = mock.Mock()
        django_response.status_code = 200

        expected_attributes = {
            'http.url': u'/',
            'http.method': 'GET',
            'http.status_code': '200',
            'django.user.id': '123',
            'django.user.name': 'test_name'
        }

        mock_user = mock.Mock()
        mock_user.pk = 123
        mock_user.get_username.return_value = 'test_name'
        django_request.user = mock_user

        middleware_obj.process_response(django_request, django_response)

        self.assertEqual(span.attributes, expected_attributes)

    def test_process_response_unfinished_child_span(self):
        from opencensus.ext.django import middleware

        trace_id = '2dd43a1d6b2549c6bc2a1a54c2fc0b05'
        span_id = '6e0c63257de34c92'
        django_trace_id = '{}/{}'.format(trace_id, span_id)

        django_request = RequestFactory().get('/', **{
            google_cloud_format._TRACE_CONTEXT_HEADER_NAME: django_trace_id})

        middleware_obj = middleware.OpencensusMiddleware()

        middleware_obj.process_request(django_request)
        tracer = middleware._get_current_tracer()
        span = tracer.current_span()

        exporter_mock = mock.Mock()
        tracer.exporter = exporter_mock

        django_response = mock.Mock()
        django_response.status_code = 500

        expected_attributes = {
            'http.url': u'/',
            'http.method': 'GET',
            'http.status_code': '500',
            'django.user.id': '123',
            'django.user.name': 'test_name'
        }

        mock_user = mock.Mock()
        mock_user.pk = 123
        mock_user.get_username.return_value = 'test_name'
        django_request.user = mock_user

        tracer.start_span()
        self.assertNotEqual(span, tracer.current_span())
        middleware_obj.process_response(django_request, django_response)

        self.assertEqual(span.attributes, expected_attributes)


class Test__set_django_attributes(unittest.TestCase):
    class Span(object):
        def __init__(self):
            self.attributes = {}

        def add_attribute(self, key, value):
            self.attributes[key] = value

    def test__set_django_attributes_no_user(self):
        from opencensus.ext.django.middleware import \
            _set_django_attributes
        span = self.Span()
        request = mock.Mock()

        request.user = None

        _set_django_attributes(span, request)

        expected_attributes = {}

        self.assertEqual(span.attributes, expected_attributes)

    def test__set_django_attributes_no_user_info(self):
        from opencensus.ext.django.middleware import \
            _set_django_attributes
        span = self.Span()
        request = mock.Mock()
        django_user = mock.Mock()

        request.user = django_user
        django_user.pk = None
        django_user.get_username.return_value = None

        _set_django_attributes(span, request)

        expected_attributes = {}

        self.assertEqual(span.attributes, expected_attributes)

    def test__set_django_attributes_with_user_info(self):
        from opencensus.ext.django.middleware import \
            _set_django_attributes
        span = self.Span()
        request = mock.Mock()
        django_user = mock.Mock()

        request.user = django_user
        test_id = 123
        test_name = 'test_name'
        django_user.pk = test_id
        django_user.get_username.return_value = test_name

        _set_django_attributes(span, request)

        expected_attributes = {
            'django.user.id': '123',
            'django.user.name': test_name}

        self.assertEqual(span.attributes, expected_attributes)
