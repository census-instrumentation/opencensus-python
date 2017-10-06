# Copyright 2017, OpenCensus Authors
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

# Environment variable set in App Engine when vm:true is set.
_APPENGINE_FLEXIBLE_ENV_VM = 'GAE_APPENGINE_HOSTNAME'

# Environment variable set in App Engine when env:flex is set.
_APPENGINE_FLEXIBLE_ENV_FLEX = 'GAE_INSTANCE'

# Stackdriver Trace common labels.
# See: https://cloud.google.com/trace/docs/reference/v1/rpc/
#      google.devtools.cloudtrace.v1#google.devtools.cloudtrace.v1.TraceSpan
STACKDRIVER_LABELS = {
    'AGENT': '/agent',
    'COMPONENT': '/component',
    'ERROR_MESSAGE': '/error/message',
    'ERROR_NAME': '/error/name',
    'HTTP_CLIENT_CITY': '/http/client_city',
    'HTTP_CLIENT_COUNTRY': '/http/client_country',
    'HTTP_CLIENT_PROTOCOL': '/http/client_protocol',
    'HTTP_CLIENT_REGION': '/http/client_region',
    'HTTP_HOST': '/http/host',
    'HTTP_METHOD': '/http/method',
    'HTTP_REDIRECTED_URL': '/http/redirected_url',
    'HTTP_REQUEST_SIZE': '/http/request/size',
    'HTTP_RESPONSE_SIZE': '/http/response/size',
    'HTTP_STATUS_CODE': '/http/status_code',
    'HTTP_URL': '/http/url',
    'HTTP_USER_AGENT': '/http/user_agent',
    'PID': '/pid',
    'STACKTRACE': '/stacktrace',
    'TID': '/tid',
}

GRPC_LABELS = {
    'GRPC_HOST_PORT': '/grpc/host/port',
    'GRPC_METHOD': '/grpc/method',
}

# GAE common labels
# See: https://cloud.google.com/appengine/docs/flexible/python/runtime#
#      environment_variables
GAE_LABELS = {
    'GAE_FLEX_VERSION': 'g.co/gae/app/version',
    'GAE_FLEX_SERVICE': 'g.co/gae/app/service',
    'GAE_FLEX_PROJECT': 'g.co/gae/app/project',
    'GAE_FLEX_INSTANCE': 'g.co/gae/app/instance',
    'GAE_FLEX_MEMORY_MB': 'g.co/gae/app/memory_mb',
    'GAE_FLEX_PORT': 'g.co/gae/app/port',
}

# GCE common labels
GCE_LABELS = {
    'GCE_INSTANCE_ID': 'g.co/gce/instanceid',
    'GCE_HOSTNAME': 'g.co/gce/hostname',
}


class LabelsHelper(object):
    """Helper class to automatically set labels."""

    def __init__(self, tracer):
        self.tracer = tracer

    def set_labels(self):
        """Automatically set labels for each environment."""
        if self.is_gae_environment():
            self.set_gae_labels()

    def set_gae_labels(self):
        """Set the GAE environment common labels."""
        for env_var, label_key in GAE_LABELS.items():
            label_value = os.environ.get(env_var)

            if label_value is not None:
                self.tracer.add_label_to_spans(label_key, label_value)

    def is_gae_environment(self):
        """Return True if the GAE related env vars is detected."""
        if (_APPENGINE_FLEXIBLE_ENV_VM in os.environ or
                _APPENGINE_FLEXIBLE_ENV_FLEX in os.environ):
            return True
