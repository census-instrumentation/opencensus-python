# Copyright 2021, OpenCensus Authors
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

import os
import unittest

import mock

from opencensus.ext.azure.extension.azure_functions import OpenCensusExtension

MOCK_APPINSIGHTS_KEY = 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee'
MOCK_AZURE_EXPORTER_CONNSTRING = (
    'InstrumentationKey=11111111-2222-3333-4444-555555555555;'
    'IngestionEndpoint=https://mock.in.applicationinsights.azure.com/'
)

class MockContext(object):
    class MockTraceContext(object):
        Tracestate = 'rojo=00f067aa0ba902b7'
        Traceparent = '00-4bf92f3577b34da6a3ce929d0e0e4736-5fd358d59f88ce45-01'

    trace_context = MockTraceContext()

class TestAzureFunctionsExtension(unittest.TestCase):
    def setUp(self):
        self._instance = OpenCensusExtension
        OpenCensusExtension.init()
        os.environ['APPINSIGHTS_INSTRUMENTATIONKEY'] = MOCK_APPINSIGHTS_KEY

    def tearDown(self):
        if 'APPINSIGHTS_INSTRUMENTATIONKEY' in os.environ:
            del os.environ['APPINSIGHTS_INSTRUMENTATIONKEY']

    @mock.patch('opencensus.ext.azure.extension.azure_functions'
                '.config_integration')
    def test_configure_method_should_setup_trace_integration(
        self,
        cfg_mock: mock.Mock
    ):
        self._instance.configure(['requests'])
        cfg_mock.trace_integrations.assert_called_once_with(['requests'])

    @mock.patch('opencensus.ext.azure.extension.azure_functions'
                '.AzureExporter')
    def test_configure_method_should_setup_azure_exporter(
        self,
        azure_exporter_mock: mock.Mock
    ):
        self._instance.configure(['requests'])
        azure_exporter_mock.assert_called_with(connection_string=None)

    @mock.patch('opencensus.ext.azure.extension.azure_functions'
                '.AzureExporter')
    def test_configure_method_shouold_setup_azure_exporter_with_connstring(
        self,
        azure_exporter_mock: mock.Mock
    ):
        self._instance.configure(['request'], MOCK_AZURE_EXPORTER_CONNSTRING)
        azure_exporter_mock.assert_called_with(
            connection_string=MOCK_AZURE_EXPORTER_CONNSTRING
        )

    def test_pre_invocation_should_warn_if_not_configured(self):
        mock_context = MockContext()
        mock_logger = mock.Mock()
        self._instance.pre_invocation_app_level(mock_logger, mock_context)
        mock_logger.warning.assert_called_once()

    def test_pre_invocation_should_attach_tracer_to_context(self):
        # Attach a mock object to exporter
        self._instance._exporter = mock.Mock()

        # Check if the tracer is attached to mock_context
        mock_context = MockContext()
        mock_logger = mock.Mock()
        self._instance.pre_invocation_app_level(mock_logger, mock_context)
        self.assertTrue(hasattr(mock_context, 'tracer'))

    def test_post_invocation_should_ignore_tracer_deallocation_if_not_set(
        self
    ):
        mock_context = MockContext()
        mock_logger = mock.Mock()
        mock_func_args = {}
        mock_func_ret = None
        self._instance.post_invocation_app_level(
            mock_logger, mock_context, mock_func_args, mock_func_ret
        )

    def test_post_invocation_should_delete_tracer_from_context(
        self
    ):
        mock_context = MockContext()
        mock_tracer = mock.Mock()
        setattr(mock_context, 'tracer', mock_tracer)
        mock_logger = mock.Mock()
        mock_func_args = {}
        mock_func_ret = None
        self._instance.post_invocation_app_level(
            mock_logger, mock_context, mock_func_args, mock_func_ret
        )
        self.assertFalse(hasattr(mock_context, 'tracer'))
