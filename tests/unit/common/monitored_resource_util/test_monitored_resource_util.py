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

import os
import unittest

import mock

from opencensus.common.monitored_resource_util import monitored_resource
from opencensus.common.monitored_resource_util import monitored_resource_util


class TestMonitoredResourceUtil(unittest.TestCase):
    def test_gke_environment(self):
        patch = mock.patch.dict(os.environ,
                                {'KUBERNETES_SERVICE_HOST': '127.0.0.1'})

        with patch:
            mr = monitored_resource_util.get_instance()

            self.assertIsNotNone(mr)
            self.assertIsInstance(mr,
                                  monitored_resource.GcpGkeMonitoredResource)

    def test_gce_environment(self):
        patch = mock.patch(
            'opencensus.common.monitored_resource_util.'
            'gcp_metadata_config.GcpMetadataConfig.'
            'is_running_on_gcp',
            return_value=True)
        with patch:
            mr = monitored_resource_util.get_instance()

            self.assertIsNotNone(mr)
            self.assertIsInstance(mr,
                                  monitored_resource.GcpGceMonitoredResource)

    @mock.patch('opencensus.common.monitored_resource_util.'
                'gcp_metadata_config.GcpMetadataConfig.is_running_on_gcp',
                return_value=False)
    @mock.patch('opencensus.common.monitored_resource_util.'
                'aws_identity_doc_utils.AwsIdentityDocumentUtils.'
                'is_running_on_aws',
                return_value=True)
    def test_aws_environment(self, aws_util_mock, gcp_metadata_mock):
        mr = monitored_resource_util.get_instance()

        self.assertIsNotNone(mr)
        self.assertIsInstance(mr, monitored_resource.AwsMonitoredResource)

    @mock.patch('opencensus.common.monitored_resource_util.'
                'gcp_metadata_config.GcpMetadataConfig.is_running_on_gcp',
                return_value=False)
    @mock.patch('opencensus.common.monitored_resource_util.'
                'aws_identity_doc_utils.AwsIdentityDocumentUtils.'
                'is_running_on_aws',
                return_value=False)
    def test_non_supported_environment(self, aws_util_mock, gcp_metadata_mock):
        mr = monitored_resource_util.get_instance()

        self.assertIsNone(mr)
