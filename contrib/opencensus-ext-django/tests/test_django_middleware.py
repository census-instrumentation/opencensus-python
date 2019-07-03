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

from django.test import RequestFactory
from django.test.utils import teardown_test_environment

from opencensus.trace import execution_context
from opencensus.trace import print_exporter
from opencensus.trace import samplers
from opencensus.trace import utils
from opencensus.trace.blank_span import BlankSpan
from opencensus.trace.propagation import trace_context_http_header_format


class TestOpencensusMiddleware(unittest.TestCase):

    def setUp(self):
        from django.conf import settings as django_settings
        from django.test.utils import setup_test_environment
        from opencensus.ext.django import middleware
        from django.http import HttpResponse
        from django.views import View

        if not django_settings.configured:
            django_settings.configure()
        setup_test_environment()

        self.middleware_kls = middleware.OpencensusMiddleware

        class MockViewError(View):
            def get(self, *args, **kwargs):
                return HttpResponse(status=500)

            def post(self, *args, **kwargs):
                return HttpResponse(status=500)

        class MockViewOk(View):
            def get(self, *args, **kwargs):
                return HttpResponse(status=200)

            def post(self, *args, **kwargs):
                return HttpResponse(status=200)

        self.view_func_error = MockViewError.as_view()
        self.view_func_ok = MockViewOk.as_view()

    def tearDown(self):
        execution_context.clear()
        teardown_test_environment()

    def test_constructor_default(self):
        middleware_obj = self.middleware_kls(mock.Mock())

        assert isinstance(middleware_obj.sampler, samplers.ProbabilitySampler)
        assert isinstance(
            middleware_obj.exporter,
            print_exporter.PrintExporter
        )
        assert isinstance(
            middleware_obj.propagator,
            trace_context_http_header_format.TraceContextPropagator,
        )

    def test_configuration(self):
        settings = type('Test', (object,), {})
        settings.OPENCENSUS = {
            'TRACE': {
                'SAMPLER': 'opencensus.trace.samplers.AlwaysOnSampler()',  # noqa
                'EXPORTER': 'opencensus.trace.print_exporter.PrintExporter()',  # noqa
                'PROPAGATOR': 'opencensus.trace.propagation.trace_context_http_header_format.TraceContextPropagator()',  # noqa
            }
        }
        patch_settings = mock.patch(
            'django.conf.settings',
            settings)

        with patch_settings:
            middleware_obj = self.middleware_kls(mock.Mock())

        assert isinstance(middleware_obj.sampler, samplers.AlwaysOnSampler)
        assert isinstance(
            middleware_obj.exporter,
            print_exporter.PrintExporter
        )
        assert isinstance(
            middleware_obj.propagator,
            trace_context_http_header_format.TraceContextPropagator,
        )

    def test_blacklist_path(self):
        execution_context.clear()

        blacklist_paths = ['test_blacklist_path']
        settings = type('Test', (object,), {})
        settings.OPENCENSUS = {
            'TRACE': {
                'SAMPLER': 'opencensus.trace.samplers.AlwaysOnSampler()',  # noqa
                'BLACKLIST_PATHS': blacklist_paths,
                'EXPORTER': mock.Mock(),
            }
        }
        patch_settings = mock.patch(
            'django.conf.settings',
            settings)

        with patch_settings:
            middleware_obj = self.middleware_kls(mock.Mock())

        django_request = RequestFactory().get('/test_blacklist_path')
        disabled = utils.disable_tracing_url(django_request.path,
                                             blacklist_paths)
        self.assertTrue(disabled)
        self.assertEqual(middleware_obj.blacklist_paths, blacklist_paths)

        # test processing request
        middleware_obj(django_request)

        tracer = execution_context.get_opencensus_tracer()
        span = tracer.current_span()

        assert isinstance(span, BlankSpan)


class TestCustomOpencensusMiddleware(TestOpencensusMiddleware):

    def setUp(self):
        from opencensus.ext.django import middleware

        super(TestCustomOpencensusMiddleware, self).setUp()

        class CustomOpencensusMiddleware(middleware.OpencensusMiddleware):
            def set_django_attributes(self, span, request, response):
                # For the purpose of span inspection, set it on the instance
                super(CustomOpencensusMiddleware, self).set_django_attributes(
                    span, request, response
                )
                self.span = span

        self.middleware_kls = CustomOpencensusMiddleware

    def test_span_attributes_get_200(self):
        from django.urls.resolvers import ResolverMatch

        trace_id = '2dd43a1d6b2549c6bc2a1a54c2fc0b05'
        span_id = '6e0c63257de34c92'
        django_trace_id = '00-{}-{}-00'.format(trace_id, span_id)

        django_request = RequestFactory().get('/', **{
            'traceparent': django_trace_id,
        })
        django_request.resolver_match = ResolverMatch(
            self.view_func_ok, None, None)

        # Force the test request to be sampled
        settings = type('Test', (object,), {})
        settings.OPENCENSUS = {
            'TRACE': {
                'SAMPLER': 'opencensus.trace.samplers.AlwaysOnSampler()',  # noqa
            }
        }
        patch_settings = mock.patch(
            'django.conf.settings',
            settings)

        with patch_settings:
            middleware_obj = self.middleware_kls(self.view_func_ok)

        tracer = execution_context.get_opencensus_tracer()

        exporter_mock = mock.Mock()
        tracer.exporter = exporter_mock

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

        middleware_obj(django_request)
        span = middleware_obj.span

        self.assertEqual(span.attributes, expected_attributes)

    def test_span_attributes_post_500(self):
        from django.urls.resolvers import ResolverMatch

        trace_id = '2dd43a1d6b2549c6bc2a1a54c2fc0b05'
        span_id = '6e0c63257de34c92'
        django_trace_id = '00-{}-{}-00'.format(trace_id, span_id)

        django_request = RequestFactory().post('/', **{
            'traceparent': django_trace_id,
        })
        django_request.resolver_match = ResolverMatch(
            self.view_func_error, None, None)

        # Force the test request to be sampled
        settings = type('Test', (object,), {})
        settings.OPENCENSUS = {
            'TRACE': {
                'SAMPLER': 'opencensus.trace.samplers.AlwaysOnSampler()',  # noqa
            }
        }
        patch_settings = mock.patch(
            'django.conf.settings',
            settings)

        with patch_settings:
            middleware_obj = self.middleware_kls(self.view_func_error)

        tracer = execution_context.get_opencensus_tracer()

        exporter_mock = mock.Mock()
        tracer.exporter = exporter_mock

        expected_attributes = {
            'http.url': u'/',
            'http.method': 'POST',
            'http.status_code': '500',
            'django.user.id': '123',
            'django.user.name': 'test_name'
        }

        mock_user = mock.Mock()
        mock_user.pk = 123
        mock_user.get_username.return_value = 'test_name'
        django_request.user = mock_user

        middleware_obj(django_request)
        span = middleware_obj.span

        self.assertEqual(span.attributes, expected_attributes)


class Test__set_django_attributes(unittest.TestCase):
    class Span(object):
        def __init__(self):
            self.attributes = {}

        def add_attribute(self, key, value):
            self.attributes[key] = value

    def test__set_django_attributes_no_user(self):
        from opencensus.ext.django.middleware import OpencensusMiddleware
        span = self.Span()
        request = mock.Mock()
        response = mock.Mock()

        request.user = None

        OpencensusMiddleware(mock.Mock()).set_django_attributes(
            span, request, response)

        expected_attributes = {}

        self.assertEqual(span.attributes, expected_attributes)

    def test__set_django_attributes_no_user_info(self):
        from opencensus.ext.django.middleware import OpencensusMiddleware
        span = self.Span()
        request = mock.Mock()
        response = mock.Mock()
        django_user = mock.Mock()

        request.user = django_user
        django_user.pk = None
        django_user.get_username.return_value = None

        OpencensusMiddleware(mock.Mock()).set_django_attributes(
            span, request, response)

        expected_attributes = {}

        self.assertEqual(span.attributes, expected_attributes)

    def test__set_django_attributes_with_user_info(self):
        from opencensus.ext.django.middleware import OpencensusMiddleware
        span = self.Span()
        request = mock.Mock()
        response = mock.Mock()
        django_user = mock.Mock()

        request.user = django_user
        test_id = 123
        test_name = 'test_name'
        django_user.pk = test_id
        django_user.get_username.return_value = test_name

        OpencensusMiddleware(mock.Mock()).set_django_attributes(
            span, request, response)

        expected_attributes = {
            'django.user.id': '123',
            'django.user.name': test_name}

        self.assertEqual(span.attributes, expected_attributes)
