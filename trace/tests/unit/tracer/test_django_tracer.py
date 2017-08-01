# Copyright 2017 Google Inc.
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


class TestDjangoTracer(unittest.TestCase):

    @mock.patch('opencensus.trace.tracer.django_tracer.get_django_header')
    @mock.patch('opencensus.trace.propagation.google_cloud_format.from_header')
    def test_constructor_default(
            self, mock_from_header, mock_get_django_header):
        from opencensus.trace import span_context
        from opencensus.trace.reporters import print_reporter
        from opencensus.trace.samplers import always_on
        from opencensus.trace.tracer import django_tracer

        trace_id = '6e0c63257de34c92bf9efcd03927272e'
        test_span_context = span_context.SpanContext(trace_id=trace_id)

        mock_from_header.return_value = test_span_context
        mock_get_django_header.return_value = 'test_django_header'

        tracer = django_tracer.DjangoTracer()

        assert isinstance(tracer.reporter, print_reporter.PrintReporter)
        assert isinstance(tracer.sampler, always_on.AlwaysOnSampler)
        assert isinstance(tracer.span_context, span_context.SpanContext)
        self.assertEqual(tracer.span_context, test_span_context)

    def test_constructor_explicit(self):
        from opencensus.trace import span_context
        from opencensus.trace.reporters import print_reporter
        from opencensus.trace.samplers import always_on
        from opencensus.trace.tracer import django_tracer

        trace_id = '6e0c63257de34c92bf9efcd03927272e'
        span_context = span_context.SpanContext(trace_id=trace_id)
        sampler = always_on.AlwaysOnSampler()
        reporter = print_reporter.PrintReporter()

        tracer = django_tracer.DjangoTracer(
            span_context=span_context,
            sampler=sampler,
            reporter=reporter)

        self.assertEqual(tracer.span_context, span_context)
        self.assertEqual(tracer.sampler, sampler)
        self.assertEqual(tracer.reporter, reporter)


class Test_get_django_header(unittest.TestCase):

    @staticmethod
    def _call_fut():
        from opencensus.trace.tracer import django_tracer

        return django_tracer.get_django_header()

    def setUp(self):
        from django.conf import settings
        from django.test.utils import setup_test_environment

        if not settings.configured:
            settings.configure()
        setup_test_environment()

    def tearDown(self):
        from django.test.utils import teardown_test_environment
        from opencensus.trace.tracer.middleware import request

        teardown_test_environment()
        request._thread_locals.__dict__.clear()

    def test_no_context_header(self):
        header = self._call_fut()
        self.assertIsNone(header)

    def test_valid_context_header(self):
        from django.test import RequestFactory
        from opencensus.trace.tracer.middleware import request

        django_trace_header = 'HTTP_X_CLOUD_TRACE_CONTEXT'
        trace_id = 'testtraceiddjango'
        django_trace_id = trace_id + '/testspanid'

        django_request = RequestFactory().get(
            '/',
            **{django_trace_header: django_trace_id})

        middleware = request.RequestMiddleware()
        middleware.process_request(django_request)
        header = self._call_fut()

        self.assertEqual(header, django_trace_id)
