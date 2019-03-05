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

import json
import mock
import unittest

from opencensus.common.monitored_resource import aws_identity_doc_utils


class TestAwsIdentityDocumentUtils(unittest.TestCase):
    @mock.patch('opencensus.common.monitored_resource.'
                'aws_identity_doc_utils.get_request')
    def test_get_aws_metadata(self, http_request_mock):
        mocked_http_response = {
            'availabilityZone': 'us-west-2b',
            'instanceId': 'i-1234567890abcdef0',
            'imageId': 'ami-5fb8c835',
            'privateIp': '10.158.112.84',
            'pendingTime': '2016-11-19T16:32:11Z',
            'accountId': '123456789012',
            'region': 'us-west-2',
            'marketplaceProductCodes': ["1abc2defghijklm3nopqrs4tu"],
            'instanceType': 't2.micro',
            'version': '2017-09-30',
            'architecture': 'x86_64',
        }

        http_request_mock.return_value = json.dumps(mocked_http_response)
        aws_identity_doc_utils.AwsIdentityDocumentUtils.inited = False
        aws_identity_doc_utils.AwsIdentityDocumentUtils.is_running = False
        aws_identity_doc_utils.aws_metadata_map = {}

        self.assertTrue(aws_identity_doc_utils.AwsIdentityDocumentUtils
                        .is_running_on_aws())

        labels_list = aws_identity_doc_utils.AwsIdentityDocumentUtils(
        ).get_aws_metadata()

        self.assertEquals(len(labels_list), 3)

        expected_labels = {
            'instance_id': 'i-1234567890abcdef0',
            'aws_account': '123456789012',
            'region': 'us-west-2'
        }

        self.assertEquals(labels_list, expected_labels)

    @mock.patch('opencensus.common.monitored_resource.'
                'aws_identity_doc_utils.get_request')
    def test_get_aws_metadata_none_fields(self, http_request_mock):
        mocked_http_response = {
            'availabilityZone': 'us-west-2b',
            'imageId': 'ami-5fb8c835',
            'privateIp': '10.158.112.84',
            'pendingTime': '2016-11-19T16:32:11Z',
            'accountId': '123456789012',
            'region': 'us-west-2',
            'marketplaceProductCodes': ["1abc2defghijklm3nopqrs4tu"],
            'instanceType': 't2.micro',
            'version': '2017-09-30',
            'architecture': 'x86_64',
        }

        http_request_mock.return_value = json.dumps(mocked_http_response)
        aws_identity_doc_utils.AwsIdentityDocumentUtils.inited = False
        aws_identity_doc_utils.AwsIdentityDocumentUtils.is_running = False
        aws_identity_doc_utils.aws_metadata_map = {}

        self.assertTrue(aws_identity_doc_utils.AwsIdentityDocumentUtils
                        .is_running_on_aws())

        labels_list = aws_identity_doc_utils.AwsIdentityDocumentUtils(
        ).get_aws_metadata()

        self.assertEquals(len(labels_list), 2)

        expected_labels = {
            'aws_account': '123456789012',
            'region': 'us-west-2'
        }

        self.assertEquals(labels_list, expected_labels)

    @mock.patch('opencensus.common.monitored_resource.'
                'aws_identity_doc_utils.get_request')
    def test_aws_not_running(self, http_request_mock):
        http_request_mock.return_value = None
        aws_identity_doc_utils.inited = False
        aws_identity_doc_utils.is_running_on_aws = False
        aws_identity_doc_utils.aws_metadata_map = {}

        self.assertFalse(aws_identity_doc_utils.AwsIdentityDocumentUtils
                         .is_running_on_aws())

        labels_list = aws_identity_doc_utils.AwsIdentityDocumentUtils(
        ).get_aws_metadata()

        self.assertEquals(len(labels_list), 0)
