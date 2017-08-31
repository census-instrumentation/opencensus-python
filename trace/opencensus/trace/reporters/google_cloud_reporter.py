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

from opencensus.trace.reporters import base

from google.cloud.trace.client import Client


class GoogleCloudReporter(base.Reporter):
    """A reporter that send traces and trace spans to Google Cloud Stackdriver
    Trace.
    """
    def __init__(self, client=None, project_id=None):
        # The client will handler the case when project_id is None
        if client is None:
            client = Client(project=project_id)

        self.client = client
        self.project_id = client.project

    def report(self, trace):
        """
        :type trace: dict
        :param trace: Trace collected.
        """
        stackdriver_traces = self.translate_to_stackdriver(trace)
        self.client.patch_traces(stackdriver_traces)

    def translate_to_stackdriver(self, trace):
        """
        :type trace: dict
        :param trace: Trace collected.

        :rtype: dict
        :returns: Traces in Google Cloud StackDriver Trace format.
        """
        trace['projectId'] = self.project_id
        traces = {'traces': [trace]}
        return traces
