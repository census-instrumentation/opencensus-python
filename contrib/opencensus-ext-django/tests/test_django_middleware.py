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
from opencensus.trace import span as span_module
from opencensus.trace import utils
from opencensus.trace.blank_span import BlankSpan
from opencensus.trace.propagation import trace_context_http_header_format


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

    def test_constructor_default(self):
        from opencensus.ext.django import middleware

        middleware = middleware.OpencensusMiddleware()

        assert isinstance(middleware.sampler, samplers.ProbabilitySampler)
        assert isinstance(middleware.exporter, print_exporter.PrintExporter)
        assert isinstance(
            middleware.propagator,
            trace_context_http_header_format.TraceContextPropagator,
        )

    def test_configuration(self):
        from opencensus.ext.django import middleware

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
            middleware = middleware.OpencensusMiddleware()

        assert isinstance(middleware.sampler, samplers.AlwaysOnSampler)
        assert isinstance(middleware.exporter, print_exporter.PrintExporter)
        assert isinstance(
            middleware.propagator,
            trace_context_http_header_format.TraceContextPropagator,
        )

    def test_process_request(self):
        from opencensus.ext.django import middleware

        trace_id = '2dd43a1d6b2549c6bc2a1a54c2fc0b05'
        span_id = '6e0c63257de34c92'
        django_trace_id = '00-{}-{}-00'.format(trace_id, span_id)

        django_request = RequestFactory().get('/wiki/Rabbit', **{
            'HTTP_TRACEPARENT': django_trace_id})

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
            middleware_obj = middleware.OpencensusMiddleware()

        # test process_request
        middleware_obj.process_request(django_request)

        tracer = middleware._get_current_tracer()

        span = tracer.current_span()

        expected_attributes = {
            'http.host': u'testserver',
            'http.method': 'GET',
            'http.path': u'/wiki/Rabbit',
            'http.route': u'/wiki/Rabbit',
            'http.url': u'http://testserver/wiki/Rabbit',
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
            middleware_obj = middleware.OpencensusMiddleware()

        django_request = RequestFactory().get('/test_blacklist_path')
        disabled = utils.disable_tracing_url(django_request.path,
                                             blacklist_paths)
        self.assertTrue(disabled)
        self.assertEqual(middleware_obj.blacklist_paths, blacklist_paths)

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
        django_trace_id = '00-{}-{}-00'.format(trace_id, span_id)

        django_request = RequestFactory().get('/wiki/Rabbit', **{
            'traceparent': django_trace_id,
        })

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
            middleware_obj = middleware.OpencensusMiddleware()

        middleware_obj.process_request(django_request)
        tracer = middleware._get_current_tracer()
        span = tracer.current_span()

        exporter_mock = mock.Mock()
        tracer.exporter = exporter_mock

        django_response = mock.Mock()
        django_response.status_code = 200

        expected_attributes = {
            'http.host': u'testserver',
            'http.method': 'GET',
            'http.path': u'/wiki/Rabbit',
            'http.route': u'/wiki/Rabbit',
            'http.url': u'http://testserver/wiki/Rabbit',
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
        django_trace_id = '00-{}-{}-00'.format(trace_id, span_id)

        django_request = RequestFactory().get('/wiki/Rabbit', **{
            'traceparent': django_trace_id,
        })

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
            middleware_obj = middleware.OpencensusMiddleware()

        middleware_obj.process_request(django_request)
        tracer = middleware._get_current_tracer()
        span = tracer.current_span()

        exporter_mock = mock.Mock()
        tracer.exporter = exporter_mock

        django_response = mock.Mock()
        django_response.status_code = 500

        expected_attributes = {
            'http.host': u'testserver',
            'http.method': 'GET',
            'http.path': u'/wiki/Rabbit',
            'http.route': u'/wiki/Rabbit',
            'http.url': u'http://testserver/wiki/Rabbit',
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
