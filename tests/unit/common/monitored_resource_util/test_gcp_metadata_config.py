# Copyright 2018, OpenCensus Authors
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
import os
import unittest

from opencensus.common.monitored_resource import gcp_metadata_config


class TestGcpMetadataConfig(unittest.TestCase):

    @mock.patch('opencensus.common.monitored_resource.'
                'gcp_metadata_config.get_request')
    def test_get_gce_metadata(self, http_request_mock):
        def assign_attribute_value(*args, **kwargs):
            attribute_uri = args[0].split('/')[-1]
            if attribute_uri == 'id':
                return 'my-instance'
            elif attribute_uri == 'project-id':
                return 'my-project'
            elif attribute_uri == 'zone':
                return '/projects/012345678/zones/us-east1'

        http_request_mock.side_effect = assign_attribute_value
        gcp_metadata_config.GcpMetadataConfig.inited = False
        gcp_metadata_config.GcpMetadataConfig.is_running = False
        gcp_metadata_config._GCP_METADATA_MAP = {}

        self.assertTrue(
            gcp_metadata_config.GcpMetadataConfig.is_running_on_gcp())

        labels_list = gcp_metadata_config.GcpMetadataConfig().get_gce_metadata(
        )

        self.assertEquals(len(labels_list), 3)

        expected_labels = {
            'instance_id': 'my-instance',
            'project_id': 'my-project',
            'zone': 'us-east1'
        }

        self.assertDictEqual(labels_list, expected_labels)

    @mock.patch('opencensus.common.monitored_resource.'
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
                return b'/projects/012345678/zones/us-east1'

        http_request_mock.side_effect = assign_attribute_value
        gcp_metadata_config.GcpMetadataConfig.inited = False
        gcp_metadata_config.GcpMetadataConfig.is_running = False
        gcp_metadata_config._GCP_METADATA_MAP = {}

        self.assertTrue(
            gcp_metadata_config.GcpMetadataConfig.is_running_on_gcp())

        labels_list = gcp_metadata_config.GcpMetadataConfig().get_gce_metadata(
        )

        self.assertEquals(len(labels_list), 3)

        expected_labels = {
            'instance_id': 'my-instance',
            'project_id': 'my-project',
            'zone': 'us-east1'
        }

        self.assertDictEqual(labels_list, expected_labels)

    @mock.patch.dict(os.environ, clear=True)
    @mock.patch('opencensus.common.monitored_resource.'
                'gcp_metadata_config.get_request')
    def test_gcp_not_running(self, http_request_mock):
        http_request_mock.return_value = None
        gcp_metadata_config.GcpMetadataConfig.inited = False
        gcp_metadata_config.GcpMetadataConfig.is_running = False
        gcp_metadata_config._GCP_METADATA_MAP = {}

        self.assertFalse(
            gcp_metadata_config.GcpMetadataConfig.is_running_on_gcp())

        self.assertEquals(
            len(gcp_metadata_config.GcpMetadataConfig().get_gce_metadata()), 0)
