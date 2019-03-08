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
            if args[0].split('/')[-1] == 'cluster-name':
                return 'cluster'
            raise AssertionError

        http_request_mock.side_effect = assign_attribute_value
        labels_list = (k8s_utils.get_k8s_metadata())
        self.assertDictEqual(
            labels_list,
            {'k8s.io/cluster/name': 'cluster',
             'k8s.io/container/name': 'container',
             'k8s.io/namespace/name': 'namespace',
             'k8s.io/pod/name': 'localhost'
             })

    @mock.patch.dict(
        os.environ, {
            'KUBERNETES_SERVICE_HOST': '127.0.0.1',
            'NAMESPACE': 'namespace',
            'HOSTNAME': 'localhost'
        },
        clear=True)
    def test_get_k8s_metadata_container_empty(self):
        labels_list = (k8s_utils.get_k8s_metadata())

        self.assertDictEqual(
            labels_list,
            {'k8s.io/namespace/name': 'namespace',
             'k8s.io/pod/name': 'localhost'
             })
