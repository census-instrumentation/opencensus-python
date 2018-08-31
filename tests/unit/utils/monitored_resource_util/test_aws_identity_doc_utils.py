# Copyright 2017 Google Inc.
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

from opencensus.utils.monitored_resource_util.aws_identity_doc_utils import \
    AwsIdentityDocumentUtils, initialize_aws_identity_document


def _mocked_requests_get(*args, **kwargs):
    class MockResponse:
        def __init__(self, content, status_code):
            self.content = content
            self.status_code = status_code

        def json(self):
            return self.content

    _SAMPLE_AWS_IDENTITY_DOCUMENT = {
        'availabilityZone': 'us-west-2b',
        'instanceId': 'i-1234567890abcdef0',
        'imageId': 'ami-5fb8c835',
        'privateIp': '10.158.112.84',
        'pendingTime': '2016-11-19T16:32:11Z',
        'accountId': '123456789012',
        'region': 'us-west-2',
        'marketplaceProductCodes': [
            "1abc2defghijklm3nopqrs4tu"
        ],
        'instanceType': 't2.micro',
        'version': '2017-09-30',
        'architecture': 'x86_64',
    }

    return MockResponse(_SAMPLE_AWS_IDENTITY_DOCUMENT, 200)


class TestAwsIdentityDocumentUtils(unittest.TestCase):

    def test_is_aws_environment_false(self):
        self.assertFalse(AwsIdentityDocumentUtils.is_aws_environment())

        labels_list = AwsIdentityDocumentUtils. \
            retrieve_aws_identity_document("aws_ec2_instance")

        self.assertEquals(len(labels_list), 0)

    def test_is_aws_environment_true(self):
        patch = mock.patch(
            'opencensus.utils.monitored_resource_util.aws_identity_doc_utils.requests.get',
            new=_mocked_requests_get)

        with patch:
            initialize_aws_identity_document()
            self.assertTrue(AwsIdentityDocumentUtils.is_aws_environment())

            labels_list = AwsIdentityDocumentUtils. \
                retrieve_aws_identity_document("g.co/r/aws_ec2_instance/")

            self.assertEquals(len(labels_list), 3)

            expected_labels = [
                {
                    'g.co/r/aws_ec2_instance/instance_id': {
                        'string_value': {
                            'truncated_byte_count': 0,
                            'value': 'i-1234567890abcdef0'
                        }
                    }
                },
                {
                    'g.co/r/aws_ec2_instance/region': {
                        'string_value': {
                            'truncated_byte_count': 0,
                            'value': 'us-west-2'
                        }
                    }
                },
                {
                    'g.co/r/aws_ec2_instance/aws_account': {
                        'string_value': {
                            'truncated_byte_count': 0,
                            'value': '123456789012'
                        }
                    }
                }
            ]

            self.assertEquals(labels_list, expected_labels)
