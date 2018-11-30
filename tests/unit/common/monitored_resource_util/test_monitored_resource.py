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

import mock
import unittest

from opencensus.common.monitored_resource_util import monitored_resource


class TestMonitoredResource(unittest.TestCase):
    @mock.patch('opencensus.common.monitored_resource_util.monitored_resource'
                '.GcpMetadataConfig')
    def test_GcpGceMonitoredResource(self, gcp_metadata_mock):
        mocked_labels = {
            'instance_id': 'my-instance',
            'project_id': 'my-project',
            'zone': 'us-east1'
        }

        gcp_metadata_mock.return_value = mock.Mock()
        gcp_metadata_mock.return_value.get_gce_metadata.return_value =\
            mocked_labels
        resource = monitored_resource.GcpGceMonitoredResource()
        self.assertEquals(resource.resource_type, 'gce_instance')
        self.assertEquals(resource.get_resource_labels(), mocked_labels)

    @mock.patch('opencensus.common.monitored_resource_util.monitored_resource'
                '.GcpMetadataConfig')
    def test_GcpGkeMonitoredResource(self, gcp_metadata_mock):

        mocked_labels = {
            'instance_id': 'my-instance',
            'cluster_name': 'cluster',
            'project_id': 'my-project',
            'zone': 'us-east1',
            'pod_id': 'localhost',
            'namespace_id': 'namespace',
            'container_name': 'container'
        }

        gcp_metadata_mock.return_value = mock.Mock()
        gcp_metadata_mock.return_value.get_gke_metadata.return_value =\
            mocked_labels
        resource = monitored_resource.GcpGkeMonitoredResource()
        self.assertEquals(resource.resource_type, 'gke_container')
        self.assertEquals(resource.get_resource_labels(), mocked_labels)

    @mock.patch('opencensus.common.monitored_resource_util.monitored_resource'
                '.AwsIdentityDocumentUtils')
    def test_AwsMonitoredResource(self, aws_metadata_mock):

        mocked_labels = {
            'instance_id': 'i-1234567890abcdef0',
            'aws_account': '123456789012',
            'region': 'us-west-2'
        }

        aws_metadata_mock.return_value = mock.Mock()
        aws_metadata_mock.return_value.get_aws_metadata.return_value =\
            mocked_labels

        resource = monitored_resource.AwsMonitoredResource()
        self.assertEquals(resource.resource_type, 'aws_ec2_instance')
        self.assertEquals(resource.get_resource_labels(), mocked_labels)
