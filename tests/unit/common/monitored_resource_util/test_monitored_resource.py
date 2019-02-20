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

from contextlib import contextmanager
import mock
import os
import unittest

from opencensus.common.monitored_resource_util import monitored_resource


@contextmanager
def mock_mr_method(method, use):
    with mock.patch('{}.{}'.format(monitored_resource.__name__, method)) as mm:
        mm.return_value = use
        yield


def mock_use_gke(use):
    return mock_mr_method('is_gke_environment', use)


def mock_use_gce(use):
    return mock_mr_method('is_gce_environment', use)


def mock_use_aws(use):
    return mock_mr_method('is_aws_environment', use)


@contextmanager
def mock_gke_env():
    with mock_use_gke(True):
        with mock_use_gce(False):
            with mock_use_aws(False):
                yield


@contextmanager
def mock_gce_env():
    with mock_use_gke(False):
        with mock_use_gce(True):
            with mock_use_aws(False):
                yield


@contextmanager
def mock_aws_env():
    with mock_use_gke(False):
        with mock_use_gce(False):
            with mock_use_aws(True):
                yield


class TestMonitoredResource(unittest.TestCase):

    @mock.patch('opencensus.common.monitored_resource_util.monitored_resource'
                '.gcp_metadata_config.GcpMetadataConfig')
    def test_gcp_gce_monitored_resource(self, gcp_metadata_mock):
        mocked_labels = {
            'instance_id': 'my-instance',
            'project_id': 'my-project',
            'zone': 'us-east1'
        }

        gcp_metadata_mock.return_value = mock.Mock()
        gcp_metadata_mock.return_value.get_gce_metadata.return_value =\
            mocked_labels
        with mock_gce_env():
            resource = monitored_resource.get_instance()
        self.assertEquals(resource.get_type(), 'gce_instance')
        self.assertEquals(resource.get_labels(), mocked_labels)

    @mock.patch('opencensus.common.monitored_resource_util.monitored_resource'
                '.gcp_metadata_config.GcpMetadataConfig')
    def test_gcp_gke_monitored_resource(self, gcp_metadata_mock):

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
        with mock_gke_env():
            resource = monitored_resource.get_instance()
        self.assertEquals(resource.get_type(), 'gke_container')
        self.assertEquals(resource.get_labels(), mocked_labels)

    @mock.patch('opencensus.common.monitored_resource_util.monitored_resource'
                '.aws_identity_doc_utils.AwsIdentityDocumentUtils')
    def test_aws_monitored_resource(self, aws_metadata_mock):

        mocked_labels = {
            'instance_id': 'i-1234567890abcdef0',
            'aws_account': '123456789012',
            'region': 'us-west-2'
        }

        aws_metadata_mock.return_value = mock.Mock()
        aws_metadata_mock.return_value.get_aws_metadata.return_value =\
            mocked_labels

        with mock_aws_env():
            resource = monitored_resource.get_instance()
        self.assertEquals(resource.get_type(), 'aws_ec2_instance')
        self.assertEquals(resource.get_labels(), mocked_labels)

    def test_gke_environment(self):
        patch = mock.patch.dict(os.environ,
                                {'KUBERNETES_SERVICE_HOST': '127.0.0.1'})

        with patch:
            mr = monitored_resource.get_instance()

            self.assertIsNotNone(mr)
            self.assertEqual(mr.get_type(), "gke_container")

    def test_gce_environment(self):
        patch = mock.patch(
            'opencensus.common.monitored_resource_util.'
            'gcp_metadata_config.GcpMetadataConfig.'
            'is_running_on_gcp',
            return_value=True)
        with patch:
            mr = monitored_resource.get_instance()

            self.assertIsNotNone(mr)
            self.assertEqual(mr.get_type(), "gce_instance")

    @mock.patch('opencensus.common.monitored_resource_util.'
                'gcp_metadata_config.GcpMetadataConfig.is_running_on_gcp',
                return_value=False)
    @mock.patch('opencensus.common.monitored_resource_util.'
                'aws_identity_doc_utils.AwsIdentityDocumentUtils.'
                'is_running_on_aws',
                return_value=True)
    def test_aws_environment(self, aws_util_mock, gcp_metadata_mock):
        mr = monitored_resource.get_instance()

        self.assertIsNotNone(mr)
        self.assertEqual(mr.get_type(), "aws_ec2_instance")

    @mock.patch('opencensus.common.monitored_resource_util.'
                'gcp_metadata_config.GcpMetadataConfig.is_running_on_gcp',
                return_value=False)
    @mock.patch('opencensus.common.monitored_resource_util.'
                'aws_identity_doc_utils.AwsIdentityDocumentUtils.'
                'is_running_on_aws',
                return_value=False)
    def test_non_supported_environment(self, aws_util_mock, gcp_metadata_mock):
        mr = monitored_resource.get_instance()

        self.assertIsNone(mr)
