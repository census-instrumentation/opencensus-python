# Copyright 2019, OpenCensus Authors
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

try:
    import mock
except ImportError:
    from unittest import mock

import os
import unittest

from opencensus.common.monitored_resource import k8s_utils


class TestK8SUtils(unittest.TestCase):

    @mock.patch.dict(
        os.environ, {
            'KUBERNETES_SERVICE_HOST': '127.0.0.1',
            'CONTAINER_NAME': 'container',
            'NAMESPACE': 'namespace',
            'HOSTNAME': 'localhost'
        },
        clear=True)
    @mock.patch('opencensus.common.monitored_resource.'
                'gcp_metadata_config.get_request')
    def test_get_k8s_metadata(self, http_request_mock):
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
        labels_list = (k8s_utils.get_k8s_metadata())
        self.assertDictEqual(
            labels_list,
            {'cluster_name': 'cluster',
             'project_id': 'my-project',
             'location': 'us-east1',
             'pod_name': 'localhost',
             'namespace_name': 'namespace',
             'container_name': 'container'
             })

    @mock.patch.dict(
        os.environ, {
            'KUBERNETES_SERVICE_HOST': '127.0.0.1',
            'NAMESPACE': 'namespace',
            'HOSTNAME': 'localhost'
        },
        clear=True)
    @mock.patch('opencensus.common.monitored_resource.'
                'gcp_metadata_config.get_request')
    def test_get_k8s_metadata_container_empty(self, http_request_mock):
        def assign_attribute_value(*args, **kwargs):
            attribute_uri = args[0].split('/')[-1]
            if attribute_uri == 'id':
                return 'my-instance'
            elif attribute_uri == 'project-id':
                return 'my-project'
            elif attribute_uri == 'zone':
                return 'us-east1'

        http_request_mock.side_effect = assign_attribute_value
        labels_list = (k8s_utils.get_k8s_metadata())

        self.assertDictEqual(
            labels_list,
            {'project_id': 'my-project',
             'location': 'us-east1',
             'pod_name': 'localhost',
             'namespace_name': 'namespace'
             })
