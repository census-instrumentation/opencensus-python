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
import os

_GCP_METADATA_URI = 'http://metadata/computeMetadata/v1/'
_GCP_METADATA_URI_HEADER = {'Metadata-Flavor': 'Google'}

_REQUEST_TIMEOUT = 2  # in secs


# GAE common attributes
# See: https://cloud.google.com/appengine/docs/flexible/python/runtime#
#      environment_variables
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

_GKE_ATTRIBUTES = {
    # cluster_name is the name for the cluster the container is running in.
    'cluster_name': 'instance/attributes/cluster-name'
}
_GKE_ATTRIBUTES.update(_GCE_ATTRIBUTES)


# Following attributes are derived from environment variables. They are
# configured via yaml file. For details refer to:
# https://cloud.google.com/kubernetes-engine/docs/tutorials/
# custom-metrics-autoscaling#exporting_metrics_from_the_application
_GKE_ENV_ATTRIBUTES = {
    # ContainerName is the name of the container.
    'container_name': 'CONTAINER_NAME',

    # namespace_id is the identifier for the cluster namespace the container
    # is running in
    'namespace_id': 'NAMESPACE',

    # pod_id is the identifier for the pod the container is running in.
    'pod_id': 'HOSTNAME'
}

_gcp_metadata_cache = {}


class GcpMetadataConfig(object):
    """GcpMetadata represents metadata retrieved from GCP (GKE and GCE)
    environment. Some attributes are retrieved from the system environment.
    """

    @classmethod
    def get_gce_metadata(cls, label_key_prefix):
        return cls._get_metadata(_GCE_ATTRIBUTES, label_key_prefix)

    @classmethod
    def get_gke_metadata(cls, label_key_prefix):
        labels_list = cls._get_metadata(_GKE_ATTRIBUTES, label_key_prefix)

        # Environment variables
        env_labels_list = cls._get_metadata(_GKE_ENV_ATTRIBUTES,
                                            label_key_prefix, True)
        if len(env_labels_list) > 0:
            labels_list.extend(env_labels_list)

        return labels_list

    @classmethod
    def _get_metadata(cls, attributes, label_key_prefix, env=False):
        labels_list = list()
        from opencensus.trace.attributes import Attributes
        for attribute_key, attribute_uri in attributes.items():

            if env:
                attribute_value = cls._get_env_attribute(attribute_uri)
            else:
                attribute_value = cls._get_attribute(attribute_uri)

            pair = {label_key_prefix + attribute_key: attribute_value}
            pair_label = Attributes(pair) \
                .format_attributes_json() \
                .get('attributeMap')

            if len(pair_label) > 0:
                labels_list.append(pair_label)

        return labels_list

    @staticmethod
    def _get_env_attribute(attribute_entry):
        return os.environ.get(attribute_entry)

    @staticmethod
    def _get_attribute(attribute_uri):

        if attribute_uri in _gcp_metadata_cache:
            return _gcp_metadata_cache[attribute_uri]

        try:
            r = requests.get(_GCP_METADATA_URI + attribute_uri,
                             headers=_GCP_METADATA_URI_HEADER,
                             timeout=_REQUEST_TIMEOUT)

            if r.status_code != 404:
                _gcp_metadata_cache[attribute_uri] = r.content
                return r.content

        except Exception as e:
            pass

        return None
