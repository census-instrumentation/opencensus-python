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

import mock

import unittest


class TestOpencensusMiddleware(unittest.TestCase):

    def setUp(self):
        from django.conf import settings as django_settings
        from django.test.utils import setup_test_environment

        if not django_settings.configured:
            django_settings.configure()
        setup_test_environment()

    def tearDown(self):
        from django.test.utils import teardown_test_environment
        from opencensus.trace import execution_context

        execution_context.clear()

        teardown_test_environment()

    def test_constructor_cloud(self):
        from opencensus.trace.ext.django import middleware
        from opencensus.trace.samplers import always_on
        from opencensus.trace.propagation import google_cloud_format

        class MockCloudExporter(object):
            def __init__(self, project_id):
                self.project_id = project_id

        MockCloudExporter.__name__ = 'GoogleCloudExporter'

        project_id = 'my_project'
        params = {
            'GCP_EXPORTER_PROJECT': project_id,
        }

        patch_params = mock.patch(
            'opencensus.trace.ext.django.config.settings.params', params)
        patch_exporter = mock.patch(
            'opencensus.trace.ext.django.config.settings.EXPORTER',
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

    def test_constructor_zipkin(self):
        from opencensus.trace.ext.django import middleware
        from opencensus.trace.samplers import always_on
        from opencensus.trace.exporters import zipkin_exporter
        from opencensus.trace.propagation import google_cloud_format

        service_name = 'test_service'
        host_name = 'test_hostname'
        port = 2333
        params = {
            'ZIPKIN_EXPORTER_SERVICE_NAME': service_name,
            'ZIPKIN_EXPORTER_HOST_NAME': host_name,
            'ZIPKIN_EXPORTER_PORT': port,
        }

        patch_zipkin = mock.patch(
            'opencensus.trace.ext.django.config.settings.EXPORTER',
            zipkin_exporter.ZipkinExporter)

        patch_params = mock.patch(
            'opencensus.trace.ext.django.config.settings.params',
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

    def test_constructor_probability_sampler(self):
        from opencensus.trace.ext.django import middleware
        from opencensus.trace.samplers import probability
        from opencensus.trace.exporters import print_exporter
        from opencensus.trace.propagation import google_cloud_format

        rate = 0.8
        params = {
            'SAMPLING_RATE': 0.8,
        }

        patch_sampler = mock.patch(
            'opencensus.trace.ext.django.config.settings.SAMPLER',
            probability.ProbabilitySampler)
        patch_exporter = mock.patch(
            'opencensus.trace.ext.django.config.settings.EXPORTER',
            print_exporter.PrintExporter)

        patch_params = mock.patch(
            'opencensus.trace.ext.django.config.settings.params',
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
        from django.test import RequestFactory

        from opencensus.trace.ext.django import middleware

        trace_id = '2dd43a1d6b2549c6bc2a1a54c2fc0b05'
        span_id = 123
        django_trace_id = '{}/{}'.format(trace_id, span_id)

        django_request = RequestFactory().get('/', **{
            middleware._DJANGO_TRACE_HEADER: django_trace_id})

        middleware_obj = middleware.OpencensusMiddleware()

        # test process_request
        middleware_obj.process_request(django_request)

        tracer = middleware._get_current_request_tracer()

        span = tracer.current_span()

        expected_labels = {
            '/http/url': u'/',
            '/http/method': 'GET',
        }
        self.assertEqual(span.labels, expected_labels)
        self.assertEqual(span.parent_span.span_id, span_id)

        span_context = tracer.span_context
        self.assertEqual(span_context.trace_id, trace_id)

        # test process_view
        view_func = mock.Mock()
        middleware_obj.process_view(django_request, view_func)

        self.assertEqual(span.name, 'mock.mock.Mock')

    def test_process_response(self):
        from django.test import RequestFactory

        from opencensus.trace.ext.django import middleware

        trace_id = '2dd43a1d6b2549c6bc2a1a54c2fc0b05'
        span_id = 123
        django_trace_id = '{}/{}'.format(trace_id, span_id)

        django_request = RequestFactory().get('/', **{
            middleware._DJANGO_TRACE_HEADER: django_trace_id})

        middleware_obj = middleware.OpencensusMiddleware()

        middleware_obj.process_request(django_request)
        tracer = middleware._get_current_request_tracer()
        span = tracer.current_span()

        exporter_mock = mock.Mock()
        tracer.exporter = exporter_mock

        django_response = mock.Mock()
        django_response.status_code = 200

        expected_labels = {
            '/http/url': u'/',
            '/http/method': 'GET',
            '/http/status_code': '200',
            '/django/user/id': '123',
            '/django/user/name': 'test_name'
        }

        mock_user = mock.Mock()
        mock_user.pk = 123
        mock_user.get_username.return_value = 'test_name'
        django_request.user = mock_user

        middleware_obj.process_response(django_request, django_response)

        self.assertEqual(span.labels, expected_labels)
        self.assertTrue(exporter_mock.export.called)


class Test__set_django_labels(unittest.TestCase):

    class Tracer(object):
        def __init__(self):
            self.labels = {}

        def add_label_to_spans(self, key, value):
            self.labels[key] = value

    def test__set_django_labels_no_user(self):
        from opencensus.trace.ext.django.middleware import _set_django_labels

        tracer = self.Tracer()
        request = mock.Mock()

        request.user = None

        _set_django_labels(tracer, request)

        expected_labels = {}

        self.assertEqual(tracer.labels, expected_labels)

    def test__set_django_labels_no_user_info(self):
        from opencensus.trace.ext.django.middleware import _set_django_labels

        tracer = self.Tracer()
        request = mock.Mock()
        django_user = mock.Mock()

        request.user = django_user
        django_user.pk = None
        django_user.get_username.return_value = None

        _set_django_labels(tracer, request)

        expected_labels = {}

        self.assertEqual(tracer.labels, expected_labels)

    def test__set_django_labels_with_user_info(self):
        from opencensus.trace.ext.django.middleware import _set_django_labels

        tracer = self.Tracer()
        request = mock.Mock()
        django_user = mock.Mock()

        request.user = django_user
        test_id = 123
        test_name = 'test_name'
        django_user.pk = test_id
        django_user.get_username.return_value = test_name

        _set_django_labels(tracer, request)

        expected_labels = {
            '/django/user/id': '123',
            '/django/user/name': test_name}

        self.assertEqual(tracer.labels, expected_labels)
