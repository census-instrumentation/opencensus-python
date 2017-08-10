# Copyright 2017 Google Inc.
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

from opencensus.trace.reporters import google_cloud_reporter

import os

# Environment variable set in App Engine when vm:true is set.
_APPENGINE_FLEXIBLE_ENV_VM = 'GAE_APPENGINE_HOSTNAME'

# Environment variable set in App Engine when env:flex is set.
_APPENGINE_FLEXIBLE_ENV_FLEX = 'GAE_INSTANCE'

_GAE_PROJECT_ENV = 'GCLOUD_PROJECT'
_GAE_SERVICE_ENV = 'GAE_SERVICE'
_GAE_VERSION_ENV = 'GAE_VERSION'


class StackdriverLabels(object):  # pragma: NO COVER
    """Stackdriver Trace common labels"""
    AGENT = '/agent'
    COMPONENT = '/component'
    ERROR_MESSAGE = '/error/message'
    ERROR_NAME = '/error/name'
    HTTP_CLIENT_CITY = '/http/client_city'
    HTTP_CLIENT_COUNTRY = '/http/client_country'
    HTTP_CLIENT_PROTOCOL = '/http/client_protocol'
    HTTP_CLIENT_REGION = '/http/client_region'
    HTTP_HOST = '/http/host'
    HTTP_METHOD = '/http/method'
    HTTP_REDIRECTED_URL = '/http/redirected_url'
    HTTP_REQUEST_SIZE = '/http/request/size'
    HTTP_RESPONSE_SIZE = '/http/response/size'
    HTTP_STATUS_CODE = '/http/status_code'
    HTTP_URL = '/http/url'
    HTTP_USER_AGENT = '/http/user_agent'
    PID = '/pid'
    STACKTRACE = '/stacktrace'
    TID = '/tid'


class GAELabels(object):  # pragma: NO COVER
    """GAE common labels"""
    GAE_VERSION = 'g.co/gae/app/version'
    GAE_SERVICE = 'g.co/gae/app/service'
    GAE_PROJECT = 'g.co/gae/app/project'


class GCELabels(object):  # pragma: NO COVER
    """GCE common labels"""
    GCE_INSTANCE_ID = 'g.co/gce/instanceid'
    GCE_HOSTNAME = 'g.co/gce/hostname'


class LabelsHelper(object):
    """Helper class to automatically set labels."""

    def __init__(self, tracer):
        self.tracer = tracer
        self.reporter = tracer.reporter

    def set_labels(self):
        """Automatically set labels for each environment."""
        if self.is_gae_environment():
            self.set_gae_labels()

        if isinstance(
                self.reporter,
                google_cloud_reporter.GoogleCloudReporter):
            self.set_stackdriver_labels()

    def set_gae_labels(self):
        """Set the GAE environment common labels."""
        gae_version = os.environ.get(_GAE_VERSION_ENV)
        gae_service = os.environ.get(_GAE_SERVICE_ENV)
        gae_project = os.environ.get(_GAE_PROJECT_ENV)

        self.tracer.add_label_to_spans(GAELabels.GAE_VERSION, gae_version)
        self.tracer.add_label_to_spans(GAELabels.GAE_SERVICE, gae_service)
        self.tracer.add_label_to_spans(GAELabels.GAE_PROJECT, gae_project)

    def is_gae_environment(self):
        """Return True if the GAE related env vars is detected."""
        if (_APPENGINE_FLEXIBLE_ENV_VM in os.environ or
                _APPENGINE_FLEXIBLE_ENV_FLEX in os.environ):
            return True

    def set_stackdriver_labels(self):
        # TODO: Find out where to get the stackdriver common labels.
        pass
