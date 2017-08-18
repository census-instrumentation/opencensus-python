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

import unittest


class TestDjangoTraceSettings(unittest.TestCase):

    def setUp(self):
        from django.conf import settings as django_settings
        from django.test.utils import setup_test_environment

        if not django_settings.configured:
            django_settings.configure()
        setup_test_environment()

    def tearDown(self):
        from django.test.utils import teardown_test_environment

        teardown_test_environment()

    def test_constructor_default(self):
        from opencensus.trace.ext.django import config

        django_trace_settings = config.DjangoTraceSettings()

        self.assertEqual(
            django_trace_settings.settings,
            config.DEFAULT_DJANGO_TRACER_CONFIG)

    def test_constructor_explicit(self):
        from django.conf import settings as django_settings
        from opencensus.trace.ext.django import config

        fake_settings = {}
        django_settings.OPENCENSUS_TRACE = fake_settings
        django_trace_settings = config.DjangoTraceSettings()

        self.assertEqual(
            django_trace_settings.settings,
            fake_settings)

    def test__getattr___invalid(self):
        from opencensus.trace.ext.django import config

        django_trace_settings = config.DjangoTraceSettings()

        with self.assertRaises(AttributeError):
            getattr(django_trace_settings, 'TEST_INVALID_ATTR')

    def test__getattr___valid(self):
        from opencensus.trace.ext.django import config
        from opencensus.trace.tracer.context_tracer import ContextTracer

        django_trace_settings = config.DjangoTraceSettings()

        tracer_class = getattr(django_trace_settings, 'TRACER')

        assert isinstance(tracer_class(), ContextTracer)
