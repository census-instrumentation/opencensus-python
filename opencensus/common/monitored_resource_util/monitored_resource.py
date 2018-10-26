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


from opencensus.common.monitored_resource_util.gcp_metadata_config \
    import GcpMetadataConfig
from opencensus.common.monitored_resource_util.aws_identity_doc_utils \
    import AwsIdentityDocumentUtils

# supported environments (resource types)
_GCE_INSTANCE = "gce_instance"
_GKE_CONTAINER = "gke_container"
_AWS_EC2_INSTANCE = "aws_ec2_instance"


class MonitoredResource(object):
    """MonitoredResource returns the resource type and resource labels.
    """

    @property
    def resource_type(self):
        """Returns the resource type this MonitoredResource.
        :return:
        """
        raise NotImplementedError  # pragma: NO COVER

    def get_resource_labels(self):
        """Returns the resource labels for this MonitoredResource.
        :return:
        """
        raise NotImplementedError  # pragma: NO COVER


class GcpGceMonitoredResource(MonitoredResource):
    """GceMonitoredResource represents gce_instance type monitored resource.
    For definition refer to
    https://cloud.google.com/monitoring/api/resources#tag_gce_instance
    """

    @property
    def resource_type(self):
        return _GCE_INSTANCE

    def get_resource_labels(self):
        gcp_config = GcpMetadataConfig()
        return gcp_config.get_gce_metadata()


class GcpGkeMonitoredResource(MonitoredResource):
    """GkeMonitoredResource represents gke_container type monitored resource.
    For definition refer to
    https://cloud.google.com/monitoring/api/resources#tag_gke_container
    """

    @property
    def resource_type(self):
        return _GKE_CONTAINER

    def get_resource_labels(self):
        gcp_config = GcpMetadataConfig()
        return gcp_config.get_gke_metadata()


class AwsMonitoredResource(MonitoredResource):
    """AwsMonitoredResource represents aws_ec2_instance type monitored resource.
    For definition refer to
    https://cloud.google.com/monitoring/api/resources#tag_aws_ec2_instance
    """
    @property
    def resource_type(self):
        return _AWS_EC2_INSTANCE

    def get_resource_labels(self):
        aws_util = AwsIdentityDocumentUtils()
        return aws_util.get_aws_metadata()
