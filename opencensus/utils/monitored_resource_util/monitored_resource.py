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


class MonitoredResource(object):
    """MonitoredResource returns the resource type and resource labels.
    """

    def get_resource_type(self):
        """Returns the resource type this MonitoredResource.
        :return:
        """
        raise NotImplementedError

    def get_resource_labels(self):
        """Returns the resource labels for this MonitoredResource.
        :return:
        """
        raise NotImplementedError

    def _get_resource_label_format(self):
        return '/g.co/r/{res_type}/'.format(res_type=self.get_resource_type())


class GcpGceMonitoredResource(MonitoredResource):
    """GceMonitoredResource represents gce_instance type monitored resource.
    For definition refer to
    https://cloud.google.com/monitoring/api/resources#tag_gce_instance
    """

    def get_resource_type(self):
        return "gce_instance"

    def get_resource_labels(self):
        from opencensus.utils.monitored_resource_util.gcp_metadata_config \
            import GcpMetadataConfig

        label_key_prefix = self._get_resource_label_format()
        return GcpMetadataConfig.get_gce_metadata(label_key_prefix)


class GcpGkeMonitoredResource(MonitoredResource):
    """GkeMonitoredResource represents gke_container type monitored resource.
    For definition refer to
    https://cloud.google.com/monitoring/api/resources#tag_gke_container
    """

    def get_resource_type(self):
        return "gke_container"

    def get_resource_labels(self):
        from opencensus.utils.monitored_resource_util.gcp_metadata_config \
            import GcpMetadataConfig

        label_key_prefix = self._get_resource_label_format()
        return GcpMetadataConfig.get_gke_metadata(label_key_prefix)


class AwsMonitoredResource(MonitoredResource):
    """AwsMonitoredResource represents aws_ec2_instance type monitored resource.
    For definition refer to
    https://cloud.google.com/monitoring/api/resources#tag_aws_ec2_instance
    """

    def get_resource_type(self):
        return "aws_ec2_instance"

    def get_resource_labels(self):
        from opencensus.utils.monitored_resource_util.aws_identity_doc_utils \
            import AwsIdentityDocumentUtils

        label_key_prefix = self._get_resource_label_format()
        return AwsIdentityDocumentUtils.retrieve_aws_identity_document(
            label_key_prefix)
