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

from opencensus.trace import config_integration


class Test_trace_integrations(unittest.TestCase):

    def test_trace_integrations_not_exist(self):
        integrations = {
            'test_not_exists': True,
        }

        integrated = config_integration.trace_integrations(integrations)

        self.assertEqual(integrated, [])

    def test_trace_integrations(self):
        mock_module = mock.Mock()
        mock_importlib = mock.Mock()
        mock_importlib.import_module.return_value = mock_module
        patch = mock.patch(
            'opencensus.trace.config_integration.importlib',
            mock_importlib)

        integration_list = ['mysql', 'postgresql']

        with patch:
            integrated = config_integration.trace_integrations(
                integration_list)

        self.assertTrue(mock_module.trace_integration.called)
        self.assertEqual(integrated, integration_list)
