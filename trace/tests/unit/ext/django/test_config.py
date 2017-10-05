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

    def test_constructor(self):
        from opencensus.trace.ext.django import config

        django_trace_settings = config.DjangoTraceSettings()

        self.assertEqual(
            django_trace_settings.settings,
            config.DEFAULT_DJANGO_TRACER_CONFIG)

    def test__getattr___invalid(self):
        from opencensus.trace.ext.django import config

        django_trace_settings = config.DjangoTraceSettings()

        with self.assertRaises(AttributeError):
            getattr(django_trace_settings, 'TEST_INVALID_ATTR')

    def test__getattr___valid(self):
        from opencensus.trace.ext.django import config
        from opencensus.trace.samplers.always_on import AlwaysOnSampler

        django_trace_settings = config.DjangoTraceSettings()

        sampler_class = getattr(django_trace_settings, 'SAMPLER')

        assert isinstance(sampler_class(), AlwaysOnSampler)


class Test_convert_to_import(unittest.TestCase):

    def test_convert_to_import(self):
        from opencensus.trace.ext.django import config

        module_name = 'module'
        class_name = 'class'
        path = '{}.{}'.format(module_name, class_name)
        mock_importlib = mock.Mock()
        mock_import_module = mock.Mock()
        mock_module = mock.Mock()
        mock_class = mock.Mock()
        setattr(mock_module, class_name, mock_class)
        mock_import_module.return_value = mock_module
        mock_importlib.import_module = mock_import_module

        patch = mock.patch(
            'opencensus.trace.ext.django.config.importlib', mock_importlib)

        with patch:
            result = config.convert_to_import(path)

        self.assertEqual(result, mock_class)

    def test_convert_to_import_error(self):
        from opencensus.trace.ext.django import config

        module_name = 'test_module'
        class_name = 'test_class'
        path = '{}.{}'.format(module_name, class_name)

        with self.assertRaises(ImportError):
            result = config.convert_to_import(path)
