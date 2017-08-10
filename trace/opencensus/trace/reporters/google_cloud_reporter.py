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

from google.cloud.trace.client import Client


class GoogleCloudReporter(object):
    """A reporter that send traces and trace spans to Google Cloud Stackdriver
    Trace.
    """

    def __init__(self, client=None, project_id=None):
        # The client will handler the case when project_id is None
        if client is None:
            client = Client(project=project_id)

        self.client = client
        self.project_id = self.client.project

    def report(self, traces):
        """
        :type traces: dict
        :param traces: Traces collected.
        """
        self.set_project_id(traces)
        self.client.patch_traces(traces)

    def set_project_id(self, traces):
        for trace in traces['traces']:
            trace['projectId'] = self.project_id
