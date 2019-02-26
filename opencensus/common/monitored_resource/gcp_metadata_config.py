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

from opencensus.common.http_handler import get_request

_GCP_METADATA_URI = 'http://metadata/computeMetadata/v1/'
_GCP_METADATA_URI_HEADER = {'Metadata-Flavor': 'Google'}

# GCE common attributes
# See: https://cloud.google.com/appengine/docs/flexible/python/runtime#environment_variables  # noqa
_GCE_ATTRIBUTES = {
    # ProjectID is the identifier of the GCP project associated with this
    # resource, such as "my-project".
    'project_id': 'project/project-id',

    # instance_id is the numeric VM instance identifier assigned by
    # Compute Engine.
    'instance_id': 'instance/id',

    # zone is the Compute Engine zone in which the VM is running.
    'zone': 'instance/zone'
}

_K8S_ATTRIBUTES = {
    # ProjectID is the identifier of the GCP project associated with this
    # resource, such as "my-project".
    'project_id': 'project/project-id',

    # location is the Compute Engine zone in which the VM is running.
    'location': 'instance/zone',

    # cluster_name is the name for the cluster the container is running in.
    'cluster_name': 'instance/attributes/cluster-name'
}

# Following attributes are derived from environment variables. They are
# configured via yaml file. For details refer to:
# https://cloud.google.com/kubernetes-engine/docs/tutorials/custom-metrics-autoscaling#exporting_metrics_from_the_application  # noqa
_K8S_ENV_ATTRIBUTES = {
    # ContainerName is the name of the container.
    'container_name': 'CONTAINER_NAME',

    # namespace_name is the identifier for the cluster namespace the container
    # is running in
    'namespace_name': 'NAMESPACE',

    # pod_name is the identifier for the pod the container is running in.
    'pod_name': 'HOSTNAME'
}

# Kubenertes environment variables
_KUBERNETES_SERVICE_HOST = 'KUBERNETES_SERVICE_HOST'

gcp_metadata_map = {}


def is_k8s_environment():
    """Whether the environment is a kubernetes container.

    The KUBERNETES_SERVICE_HOST environment variable must be set.
    """
    return _KUBERNETES_SERVICE_HOST in os.environ


class GcpMetadataConfig(object):
    """GcpMetadata represents metadata retrieved from GCP (GKE and GCE)
    environment. Some attributes are retrieved from the system environment.
    see : <a href="https://cloud.google.com/compute/docs/
    storing-retrieving-metadata"> https://cloud.google.com/compute/docs/storing
    -retrieving-metadata</a>
    """
    inited = False
    is_running = False

    @classmethod
    def _initialize_metadata_service(cls):
        """Initialize metadata service once and load gcp metadata into map
        This method should only be called once.
        """
        if cls.inited:
            return

        instance_id = cls._get_attribute('instance_id')

        if instance_id is not None:
            cls.is_running = True

            gcp_metadata_map['instance_id'] = instance_id

            attributes = _GCE_ATTRIBUTES
            if is_k8s_environment():
                attributes = _K8S_ATTRIBUTES

            # fetch attributes from metadata request
            for attribute_key, attribute_uri in attributes.items():
                if attribute_key not in gcp_metadata_map:
                    attribute_value = cls._get_attribute(attribute_key)
                    if attribute_value is not None:
                        gcp_metadata_map[attribute_key] = attribute_value

        cls.inited = True

    @classmethod
    def is_running_on_gcp(cls):
        cls._initialize_metadata_service()
        return cls.is_running

    def get_gce_metadata(self):
        """for GCP GCE instance"""
        if self.is_running_on_gcp():
            return gcp_metadata_map

        return dict()

    def get_k8s_metadata(self):
        """Get kubernetes container metadata, as on GCP GKE."""
        k8s_metadata = {}

        if self.is_running_on_gcp():
            k8s_metadata = gcp_metadata_map

        # fetch attributes from Environment Variables
        for attribute_key, attribute_env in _K8S_ENV_ATTRIBUTES.items():
            attribute_value = os.environ.get(attribute_env)
            if attribute_value is not None:
                k8s_metadata[attribute_key] = attribute_value

        return k8s_metadata

    @staticmethod
    def _get_attribute(attribute_key):
        """
        Fetch the requested instance metadata entry.
        :param attribute_uri: attribute_uri: attribute name relative to the
        computeMetadata/v1 prefix
        :return:  The value read from the metadata service or None
        """
        if is_k8s_environment():
            try:
                attr_slug = _K8S_ATTRIBUTES[attribute_key]
            except KeyError:
                attr_slug = _GCE_ATTRIBUTES[attribute_key]
        else:
            attr_slug = _GCE_ATTRIBUTES[attribute_key]
        attribute_value = get_request(_GCP_METADATA_URI + attr_slug,
                                      _GCP_METADATA_URI_HEADER)

        if attribute_value is not None and isinstance(attribute_value, bytes):
            # At least in python3, bytes are are returned from
            # urllib (although the response is text), convert
            # to a normal string:
            attribute_value = attribute_value.decode('utf-8')

        return attribute_value
