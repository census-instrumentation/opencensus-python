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

from contextlib import contextmanager
import os
import sys

from opencensus.common.monitored_resource import monitored_resource

if sys.version_info < (3,):
    import unittest2 as unittest
    import mock
else:
    import unittest
    from unittest import mock


@contextmanager
def mock_mr_method(method, use):
    with mock.patch('{}.{}'.format(monitored_resource.__name__, method)) as mm:
        mm.return_value = use
        yield


def mock_use_k8s(use):
    return mock_mr_method('k8s_utils.is_k8s_environment', use)


def mock_use_gce(use):
    return mock_mr_method('is_gce_environment', use)


def mock_use_aws(use):
    return mock_mr_method('is_aws_environment', use)


def mock_oc_env():
    return mock.patch.dict('os.environ', {
        'OC_RESOURCE_TYPE': 'mock_resource_type',
        'OC_RESOURCE_LABELS': 'mock_label_key=mock_label_value'
    })


@contextmanager
def mock_k8s_env():
    with mock_use_k8s(True):
        yield


@contextmanager
def mock_gce_env():
    with mock_use_gce(True):
        with mock_use_aws(False):
            yield


@contextmanager
def mock_aws_env():
    with mock_use_gce(False):
        with mock_use_aws(True):
            yield


class TestMonitoredResource(unittest.TestCase):

    def setUp(self):
        self.env_mock = mock.patch.dict(os.environ, clear=True)
        self.env_mock.start()

    def tearDown(self):
        self.env_mock.stop()

    @mock.patch('opencensus.common.monitored_resource.monitored_resource'
                '.gcp_metadata_config.GcpMetadataConfig')
    def test_gcp_gce_monitored_resource(self, gcp_md_mock):
        mocked_labels = {
            'instance_id': 'my-instance',
            'project_id': 'my-project',
            'zone': 'us-east1'
        }

        gcp_md_mock.return_value = mock.Mock()
        gcp_md_mock.return_value.get_gce_metadata.return_value = mocked_labels

        with mock_gce_env():
            resource = monitored_resource.get_instance()
        self.assertEqual(resource.get_type(), 'gce_instance')
        self.assertEqual(resource.get_labels(), mocked_labels)

        with mock_oc_env():
            with mock_gce_env():
                resource = monitored_resource.get_instance()
        self.assertEqual(resource.get_type(), 'mock_resource_type')
        self.assertDictContainsSubset(
            {'mock_label_key': 'mock_label_value'}, resource.get_labels())
        self.assertDictContainsSubset(mocked_labels, resource.get_labels())

    @mock.patch('opencensus.common.monitored_resource.monitored_resource'
                '.gcp_metadata_config.GcpMetadataConfig')
    def test_gcp_k8s_monitored_resource(self, gcp_md_mock):

        mocked_labels = {
            'instance_id': 'my-instance',
            'cluster_name': 'cluster',
            'project_id': 'my-project',
            'zone': 'us-east1',
            'pod_id': 'localhost',
            'namespace_id': 'namespace',
            'container_name': 'container'
        }
        cluster_name_key = 'instance/attributes/cluster-name'
        cluster_name_val = 'cluster'
        gcp_md_mock.return_value = mock.Mock()
        gcp_md_mock.return_value.get_gce_metadata.return_value = mocked_labels
        gcp_md_mock.get_attribute.return_value = cluster_name_val

        with mock_k8s_env():
            r1 = monitored_resource.get_instance()

        gcp_md_mock.get_attribute.assert_called_once_with(cluster_name_key)
        self.assertEqual(r1.get_type(), 'k8s_container')
        self.assertDictContainsSubset(mocked_labels, r1.get_labels())

        with mock_oc_env():
            with mock_k8s_env():
                r2 = monitored_resource.get_instance()

        self.assertEqual(r1.get_type(), 'k8s_container')
        self.assertDictContainsSubset(mocked_labels, r1.get_labels())
        self.assertDictContainsSubset(
            {'mock_label_key': 'mock_label_value'}, r2.get_labels())

    @mock.patch('opencensus.common.monitored_resource.monitored_resource'
                '.aws_identity_doc_utils.AwsIdentityDocumentUtils')
    def test_aws_monitored_resource(self, aws_md_mock):

        mocked_labels = {
            'instance_id': 'i-1234567890abcdef0',
            'aws_account': '123456789012',
            'region': 'us-west-2'
        }

        aws_md_mock.return_value = mock.Mock()
        aws_md_mock.return_value.get_aws_metadata.return_value = mocked_labels

        with mock_aws_env():
            resource = monitored_resource.get_instance()
        self.assertEqual(resource.get_type(), 'aws_ec2_instance')
        self.assertEqual(resource.get_labels(), mocked_labels)

        with mock_oc_env():
            with mock_aws_env():
                resource = monitored_resource.get_instance()
        self.assertEqual(resource.get_type(), 'mock_resource_type')
        self.assertDictContainsSubset(
            {'mock_label_key': 'mock_label_value'}, resource.get_labels())
        self.assertDictContainsSubset(mocked_labels, resource.get_labels())

    def test_k8s_environment(self):
        patch = mock.patch.dict(os.environ,
                                {'KUBERNETES_SERVICE_HOST': '127.0.0.1'})

        with patch:
            mr = monitored_resource.get_instance()

            self.assertIsNotNone(mr)
            self.assertEqual(mr.get_type(), "k8s_container")

    def test_gce_environment(self):
        patch = mock.patch(
            'opencensus.common.monitored_resource.'
            'gcp_metadata_config.GcpMetadataConfig.'
            'is_running_on_gcp',
            return_value=True)
        with patch:
            mr = monitored_resource.get_instance()

            self.assertIsNotNone(mr)
            self.assertEqual(mr.get_type(), "gce_instance")

    @mock.patch('opencensus.common.monitored_resource.'
                'gcp_metadata_config.GcpMetadataConfig.is_running_on_gcp',
                return_value=False)
    @mock.patch('opencensus.common.monitored_resource.'
                'aws_identity_doc_utils.AwsIdentityDocumentUtils.'
                'is_running_on_aws',
                return_value=True)
    def test_aws_environment(self, aws_util_mock, gcp_md_mock):
        mr = monitored_resource.get_instance()

        self.assertIsNotNone(mr)
        self.assertEqual(mr.get_type(), "aws_ec2_instance")

    @mock.patch('opencensus.common.monitored_resource.'
                'gcp_metadata_config.GcpMetadataConfig.is_running_on_gcp',
                return_value=False)
    @mock.patch('opencensus.common.monitored_resource.'
                'aws_identity_doc_utils.AwsIdentityDocumentUtils.'
                'is_running_on_aws',
                return_value=False)
    def test_non_supported_environment(self, aws_util_mock, gcp_md_mock):
        mr = monitored_resource.get_instance()
        self.assertIsNone(mr)

        with mock_oc_env():
            mr = monitored_resource.get_instance()
        self.assertIsNotNone(mr)
        self.assertEqual(mr.get_type(), 'mock_resource_type')
        self.assertDictEqual(
            mr.get_labels(), {'mock_label_key': 'mock_label_value'})
