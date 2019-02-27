# Copyright 2019, OpenCensus Authors
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

from opencensus.common.monitored_resource import gcp_metadata_config

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
    # The name of the container.
    'container_name': 'CONTAINER_NAME',

    # The identifier for the cluster namespace the container is running in
    'namespace_name': 'NAMESPACE',

    # The identifier for the pod the container is running in
    'pod_name': 'HOSTNAME'
}

# Kubenertes environment variables
_KUBERNETES_SERVICE_HOST = 'KUBERNETES_SERVICE_HOST'


def is_k8s_environment():
    """Whether the environment is a kubernetes container.

    The KUBERNETES_SERVICE_HOST environment variable must be set.
    """
    return _KUBERNETES_SERVICE_HOST in os.environ


def get_k8s_metadata():
    """Get kubernetes container metadata, as on GCP GKE."""
    k8s_metadata = {}

    for attribute_key, attribute_uri in _K8S_ATTRIBUTES.items():
        attribute_value = (gcp_metadata_config.GcpMetadataConfig
                           .get_attribute(attribute_uri))
        if attribute_value is not None:
            k8s_metadata[attribute_key] = attribute_value

    for attribute_key, attribute_env in _K8S_ENV_ATTRIBUTES.items():
        attribute_value = os.environ.get(attribute_env)
        if attribute_value is not None:
            k8s_metadata[attribute_key] = attribute_value

    return k8s_metadata
