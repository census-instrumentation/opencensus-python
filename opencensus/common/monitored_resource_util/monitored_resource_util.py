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
from opencensus.common.monitored_resource_util import monitored_resource
from opencensus.common.monitored_resource_util.aws_identity_doc_utils \
    import AwsIdentityDocumentUtils

from opencensus.common.monitored_resource_util.gcp_metadata_config \
    import GcpMetadataConfig

# Kubenertes environment variables
_KUBERNETES_SERVICE_HOST = 'KUBERNETES_SERVICE_HOST'


class MonitoredResourceUtil(object):
    """Utilities for auto detecting monitored resource based on the
    environment where the application is running.
    """

    @staticmethod
    def get_instance():
        """
        Returns a self-configured monitored resource, or None if the
        application is not running on a supported environment.
        It supports following environments (resource types)
        1. gke_container:
        2. gce_instance:
        3. aws_ec2_instance:
        :return: MonitoredResource or None
        """
        if is_gke_environment():
            return monitored_resource.GcpGkeMonitoredResource()
        elif is_gce_environment():
            return monitored_resource.GcpGceMonitoredResource()
        elif is_aws_environment():
            return monitored_resource.AwsMonitoredResource()

        return None


def is_gke_environment():
    """A Google Container Engine (GKE) container instance.
    KUBERNETES_SERVICE_HOST environment variable must be set.
    """
    return _KUBERNETES_SERVICE_HOST in os.environ


def is_gce_environment():
    """A virtual machine instance hosted in Google Compute Engine (GCE)."""
    return GcpMetadataConfig.is_running_on_gcp()


def is_aws_environment():
    """A virtual machine instance in Amazon EC2"""
    return AwsIdentityDocumentUtils.is_running_on_aws()
