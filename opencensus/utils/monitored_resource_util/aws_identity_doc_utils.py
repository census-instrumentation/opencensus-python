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

import requests

# AWS provides Instance Metadata via below url
_AWS_INSTANCE_IDENTITY_DOCUMENT_URI = \
    "http://169.254.169.254/latest/dynamic/instance-identity/document"

_REQUEST_TIMEOUT = 2  # in secs

_AWS_ATTRIBUTES = {

    # Region is the AWS region for the VM. The format of this field is
    # "aws:{region}", where supported values for {region} are listed at
    # http://docs.aws.amazon.com/general/latest/gr/rande.html.
    'region': 'region',

    # accountId is the AWS account number for the VM.
    'accountId': 'aws_account',

    # instanceId is the instance id of the instance.
    'instanceId': 'instance_id'
}

_aws_metadata_cache = {}

_aws_identity_document = 'aws_identity_document'


def initialize_aws_identity_document():
    try:
        r = requests.get(_AWS_INSTANCE_IDENTITY_DOCUMENT_URI,
                         timeout=_REQUEST_TIMEOUT)
        if r.status_code != 404:
            _aws_metadata_cache[_aws_identity_document] = r.json()

    except Exception as e:
        pass


class AwsIdentityDocumentUtils(object):
    """Util methods for getting and parsing AWS instance identity document.
    """

    initialize_aws_identity_document()

    @staticmethod
    def is_aws_environment():
        """If the environment is AWS EC2 Instance then a valid document
        is retrieved.
        :return: True or False
        """
        if _aws_identity_document in _aws_metadata_cache:
            return True

        return False

    @staticmethod
    def retrieve_aws_identity_document(label_key_prefix):
        """AWS Instance Identity Document is a JSON file.
        See docs.aws.amazon.com/AWSEC2/latest/UserGuide/
        instance-identity-documents.html.
        :param label_key_prefix:
        :return:
        """
        labels_list = []
        if _aws_identity_document in _aws_metadata_cache:
            from opencensus.trace.attributes import Attributes

            aws_env = _aws_metadata_cache[_aws_identity_document]
            for env_var, attribute_key in _AWS_ATTRIBUTES.items():
                attribute_value = aws_env.get(env_var)

                if attribute_value:
                    pair = {label_key_prefix + attribute_key: attribute_value}
                    pair_label = Attributes(pair) \
                        .format_attributes_json() \
                        .get('attributeMap')

                    if len(pair_label) > 0:
                        labels_list.append(pair_label)

        return labels_list
