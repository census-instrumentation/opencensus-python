# Copyright 2018 Google Inc.
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
import os
from opencensus.common.monitored_resource_util.monitored_resource_util import MonitoredResourceUtil
from opencensus.common.monitored_resource_util.monitored_resource import GcpGkeMonitoredResource
from opencensus.common.monitored_resource_util.monitored_resource import GcpGceMonitoredResource
from opencensus.common.monitored_resource_util.monitored_resource import AwsMonitoredResource


class TestMonitoredResourceUtil(unittest.TestCase):

    def test_gke_environment(self):
        patch = mock.patch.dict(os.environ, {'KUBERNETES_SERVICE_HOST': '127.0.0.1'})

        with patch:
            monitored_resource = MonitoredResourceUtil.get_instance()

            self.assertIsNotNone(monitored_resource)
            self.assertIsInstance(monitored_resource, GcpGkeMonitoredResource)

    def test_gce_environment(self):
        patch = mock.patch('opencensus.common.monitored_resource_util.'
                           'gcp_metadata_config.GcpMetadataConfig.'
                           'is_running_on_gcp',
                           return_value=True)
        with patch:
            monitored_resource = MonitoredResourceUtil.get_instance()

            self.assertIsNotNone(monitored_resource)
            self.assertIsInstance(monitored_resource, GcpGceMonitoredResource)

    @mock.patch('opencensus.common.monitored_resource_util.'
                'gcp_metadata_config.GcpMetadataConfig.is_running_on_gcp',
                return_value=False)
    @mock.patch('opencensus.common.monitored_resource_util.'
                'aws_identity_doc_utils.AwsIdentityDocumentUtils.'
                'is_running_on_aws',
                return_value=True)
    def test_aws_environment(self, aws_util_mock, gcp_metadata_mock):
        monitored_resource = MonitoredResourceUtil.get_instance()

        self.assertIsNotNone(monitored_resource)
        self.assertIsInstance(monitored_resource, AwsMonitoredResource)

    @mock.patch('opencensus.common.monitored_resource_util.'
                'gcp_metadata_config.GcpMetadataConfig.is_running_on_gcp',
                return_value=False)
    @mock.patch('opencensus.common.monitored_resource_util.'
                'aws_identity_doc_utils.AwsIdentityDocumentUtils.'
                'is_running_on_aws',
                return_value=False)
    def test_non_supported_environment(self, aws_util_mock, gcp_metadata_mock):
        monitored_resource = MonitoredResourceUtil.get_instance()

        self.assertIsNone(monitored_resource)
