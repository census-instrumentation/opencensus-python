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
from opencensus.common.monitored_resource_util.gcp_metadata_config \
    import GcpMetadataConfig
from opencensus.common.monitored_resource_util import gcp_metadata_config


class TestGcpMetadataConfig(unittest.TestCase):

    @mock.patch('opencensus.common.monitored_resource_util.'
                'gcp_metadata_config.get_request')
    def test_get_gce_metadata(self, http_request_mock):

        def assign_attribute_value(*args, **kwargs):
            attribute_uri = args[0].split('/')[-1]
            if attribute_uri == 'id':
                return 'my-instance'
            elif attribute_uri == 'project-id':
                return 'my-project'
            elif attribute_uri == 'zone':
                return 'us-east1'

        http_request_mock.side_effect = assign_attribute_value
        GcpMetadataConfig.inited = False
        GcpMetadataConfig.is_running = False
        gcp_metadata_config.gcp_metadata_map = {}

        self.assertTrue(GcpMetadataConfig.is_running_on_gcp())

        labels_list = GcpMetadataConfig().get_gce_metadata()

        self.assertEquals(len(labels_list), 3)

        expected_labels = {
            'instance_id': 'my-instance',
            'project_id': 'my-project',
            'zone': 'us-east1'
        }

        self.assertEquals(labels_list, expected_labels)

    @mock.patch('opencensus.common.monitored_resource_util.'
                'gcp_metadata_config.get_request')
    def test_get_gce_metadata_binary_strings(self, http_request_mock):
        """
        At least in python 3 binary strings are returned from urllib
        """
        def assign_attribute_value(*args, **kwargs):
            attribute_uri = args[0].split('/')[-1]
            if attribute_uri == 'id':
                return b'my-instance'
            elif attribute_uri == 'project-id':
                return b'my-project'
            elif attribute_uri == 'zone':
                return b'us-east1'

        http_request_mock.side_effect = assign_attribute_value
        GcpMetadataConfig.inited = False
        GcpMetadataConfig.is_running = False
        gcp_metadata_config.gcp_metadata_map = {}

        self.assertTrue(GcpMetadataConfig.is_running_on_gcp())

        labels_list = GcpMetadataConfig().get_gce_metadata()

        self.assertEquals(len(labels_list), 3)

        expected_labels = {
            'instance_id': 'my-instance',
            'project_id': 'my-project',
            'zone': 'us-east1'
        }

        self.assertEquals(labels_list, expected_labels)

    @mock.patch.dict(os.environ,
                     {'KUBERNETES_SERVICE_HOST': '127.0.0.1',
                      'CONTAINER_NAME': 'container',
                      'NAMESPACE': 'namespace',
                      'HOSTNAME': 'localhost'}, clear=True
                     )
    @mock.patch('opencensus.common.monitored_resource_util.'
                'gcp_metadata_config.get_request')
    def test_get_gke_metadata(self, http_request_mock):

        def assign_attribute_value(*args, **kwargs):
            attribute_uri = args[0].split('/')[-1]
            if attribute_uri == 'id':
                return 'my-instance'
            elif attribute_uri == 'project-id':
                return 'my-project'
            elif attribute_uri == 'cluster-name':
                return 'cluster'
            elif attribute_uri == 'zone':
                return 'us-east1'

        http_request_mock.side_effect = assign_attribute_value
        GcpMetadataConfig.inited = False
        GcpMetadataConfig.is_running = False
        gcp_metadata_config.gcp_metadata_map = {}

        self.assertTrue(GcpMetadataConfig.is_running_on_gcp())

        labels_list = GcpMetadataConfig().get_gke_metadata()

        self.assertEquals(len(labels_list), 7)

        expected_labels = {
            'instance_id': 'my-instance',
            'cluster_name': 'cluster',
            'project_id': 'my-project',
            'zone': 'us-east1',
            'pod_id': 'localhost',
            'namespace_id': 'namespace',
            'container_name': 'container'
        }

        self.assertEquals(labels_list, expected_labels)

    @mock.patch.dict(os.environ,
                     {'KUBERNETES_SERVICE_HOST': '127.0.0.1',
                      'NAMESPACE': 'namespace',
                      'HOSTNAME': 'localhost'}, clear=True
                     )
    @mock.patch('opencensus.common.monitored_resource_util.'
                'gcp_metadata_config.get_request')
    def test_get_gke_metadata_container_empty(self, http_request_mock):

        def assign_attribute_value(*args, **kwargs):
            attribute_uri = args[0].split('/')[-1]
            if attribute_uri == 'id':
                return 'my-instance'
            elif attribute_uri == 'project-id':
                return 'my-project'
            elif attribute_uri == 'zone':
                return 'us-east1'

        http_request_mock.side_effect = assign_attribute_value
        GcpMetadataConfig.inited = False
        GcpMetadataConfig.is_running = False
        gcp_metadata_config.gcp_metadata_map = {}

        self.assertTrue(GcpMetadataConfig.is_running_on_gcp())

        labels_list = GcpMetadataConfig().get_gke_metadata()

        self.assertEquals(len(labels_list), 5)

        expected_labels = {
            'instance_id': 'my-instance',
            'project_id': 'my-project',
            'zone': 'us-east1',
            'pod_id': 'localhost',
            'namespace_id': 'namespace'
        }

        self.assertEquals(labels_list, expected_labels)

    @mock.patch.dict(os.environ, clear=True)
    @mock.patch('opencensus.common.monitored_resource_util.'
                'gcp_metadata_config.get_request')
    def test_gcp_not_running(self, http_request_mock):
        http_request_mock.return_value = None
        GcpMetadataConfig.inited = False
        GcpMetadataConfig.is_running = False
        gcp_metadata_config.gcp_metadata_map = {}

        self.assertFalse(GcpMetadataConfig.is_running_on_gcp())

        self.assertEquals(len(GcpMetadataConfig().get_gce_metadata()), 0)
        self.assertEquals(len(GcpMetadataConfig().get_gke_metadata()), 0)
