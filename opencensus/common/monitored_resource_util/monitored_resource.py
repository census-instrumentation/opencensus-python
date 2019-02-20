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

import os

from opencensus.common.monitored_resource_util import aws_identity_doc_utils
from opencensus.common.monitored_resource_util import gcp_metadata_config
from opencensus.common import resource


# supported environments (resource types)
_GCE_INSTANCE = "gce_instance"
_GKE_CONTAINER = "gke_container"
_AWS_EC2_INSTANCE = "aws_ec2_instance"

# Kubenertes environment variables
_KUBERNETES_SERVICE_HOST = 'KUBERNETES_SERVICE_HOST'


def is_gke_environment():
    """A Google Container Engine (GKE) container instance.
    KUBERNETES_SERVICE_HOST environment variable must be set.
    """
    return _KUBERNETES_SERVICE_HOST in os.environ


def is_gce_environment():
    """A virtual machine instance hosted in Google Compute Engine (GCE)."""
    return gcp_metadata_config.GcpMetadataConfig.is_running_on_gcp()


def is_aws_environment():
    """A virtual machine instance in Amazon EC2"""
    return aws_identity_doc_utils.AwsIdentityDocumentUtils.is_running_on_aws()


def get_instance():
    """Get a monitored resource based on the application environment.

    Returns a self-configured monitored resource, or None if the application is
    not running on a supported environment.

    It supports following environments (resource types)
    1. gke_container:
    2. gce_instance:
    3. aws_ec2_instance:

    AwsMonitoredResource represents aws_ec2_instance type monitored resource.
    For definition refer to
    https://cloud.google.com/monitoring/api/resources#tag_aws_ec2_instance

    GkeMonitoredResource represents gke_container type monitored resource.
    For definition refer to
    https://cloud.google.com/monitoring/api/resources#tag_gke_container

    GceMonitoredResource represents gce_instance type monitored resource.
    For definition refer to
    https://cloud.google.com/monitoring/api/resources#tag_gce_instance

    :return: MonitoredResource or None
    """
    if is_gke_environment():
        return resource.Resource(
            _GKE_CONTAINER,
            gcp_metadata_config.GcpMetadataConfig().get_gke_metadata())
    if is_gce_environment():
        return resource.Resource(
            _GCE_INSTANCE,
            gcp_metadata_config.GcpMetadataConfig().get_gce_metadata())
    if is_aws_environment():
        return resource.Resource(
            _AWS_EC2_INSTANCE,
            (aws_identity_doc_utils.AwsIdentityDocumentUtils()
             .get_aws_metadata()))

    return None
