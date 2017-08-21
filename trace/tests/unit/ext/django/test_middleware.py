# Copyright 2017 Google Inc. All Rights Reserved.
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
        from opencensus.trace.ext.django import middleware

        teardown_test_environment()
        middleware._thread_locals.__dict__.clear()

    def test_constructor(self):
        from opencensus.trace.ext.django import middleware
        from opencensus.trace.samplers import always_on
        from opencensus.trace.tracer import context_tracer
        from opencensus.trace.reporters import print_reporter

        middleware = middleware.OpencensusMiddleware()

        self.assertIs(middleware._tracer, context_tracer.ContextTracer)
        self.assertIs(middleware._sampler, always_on.AlwaysOnSampler)
        self.assertIs(middleware._reporter, print_reporter.PrintReporter)

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
        self.assertEqual(len(tracer._span_stack), 1)

        span = tracer._span_stack[-1]

        expected_labels = {
            '/http/url': u'/',
            '/http/method': 'GET',
        }
        self.assertEqual(span.labels, expected_labels)
        self.assertEqual(span.parent_span_id, span_id)

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
        span = tracer._span_stack[-1]

        reporter_mock = mock.Mock()
        tracer.reporter = reporter_mock

        django_response = mock.Mock()
        django_response.status_code = 200

        expected_labels = {
            '/http/url': u'/',
            '/http/method': 'GET',
            '/http/status_code': 200,
        }

        mock_user_no_info = mock.Mock()
        mock_user_no_info.pk = None
        mock_user_no_info.get_username.return_value = None
        django_request.user = mock_user_no_info

        middleware_obj.process_response(django_request, django_response)

        self.assertEqual(span.labels, expected_labels)
        self.assertTrue(reporter_mock.report.called)
