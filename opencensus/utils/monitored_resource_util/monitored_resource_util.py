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

from opencensus.utils.monitored_resource_util import monitored_resource

# Environment variable set in App Engine when vm:true is set.
_APPENGINE_FLEXIBLE_ENV_VM = 'GAE_APPENGINE_HOSTNAME'

# Environment variable set in App Engine when env:flex is set.
_APPENGINE_FLEXIBLE_ENV_FLEX = 'GAE_INSTANCE'

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
        elif is_gae_environment():
            return monitored_resource.GcpGceMonitoredResource()
        elif is_aws_environment():
            return monitored_resource.AwsMonitoredResource()

        return None


def is_gke_environment():
    if _KUBERNETES_SERVICE_HOST in os.environ:
        return True
    return False


def is_gae_environment():
    """Return True if the GAE related env vars is detected."""
    if (_APPENGINE_FLEXIBLE_ENV_VM in os.environ or
            _APPENGINE_FLEXIBLE_ENV_FLEX in os.environ):
        return True
    return False


def is_aws_environment():
    from opencensus.utils.monitored_resource_util.aws_identity_doc_utils \
        import AwsIdentityDocumentUtils

    return AwsIdentityDocumentUtils.is_aws_environment()
