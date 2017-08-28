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

import unittest

import mock

from opencensus.trace.reporters import google_cloud_reporter


class _Client(object):
    def __init__(self, project=None):
        if project is None:
            project = 'PROJECT'

        self.project = project


class TestGoogleCloudReporter(unittest.TestCase):

    def test_constructor_default(self):
        patch = mock.patch(
            'opencensus.trace.reporters.google_cloud_reporter.Client',
            new=_Client)

        with patch:
            reporter = google_cloud_reporter.GoogleCloudReporter()

        project_id = 'PROJECT'
        self.assertEqual(reporter.project_id, project_id)

    def test_constructor_explicit(self):
        client = mock.Mock()
        project_id = 'PROJECT'
        client.project = project_id

        reporter = google_cloud_reporter.GoogleCloudReporter(
            client=client,
            project_id=project_id)

        self.assertIs(reporter.client, client)
        self.assertEqual(reporter.project_id, project_id)

    def test_report(self):
        trace = {'spans': [], 'traceId': '6e0c63257de34c92bf9efcd03927272e'}

        client = mock.Mock()
        project_id = 'PROJECT'
        client.project = project_id

        reporter = google_cloud_reporter.GoogleCloudReporter(
            client=client,
            project_id=project_id)

        reporter.report(trace)

        trace['projectId'] = project_id
        traces = {'traces': [trace]}

        client.patch_traces.assert_called_with(traces)
        self.assertTrue(client.patch_traces.called)

    def test_translate_to_stackdriver(self):
        project_id = 'PROJECT'
        trace = {'spans': [], 'traceId': '6e0c63257de34c92bf9efcd03927272e'}

        client = mock.Mock()
        client.project = project_id
        reporter = google_cloud_reporter.GoogleCloudReporter(
            client=client,
            project_id=project_id)


        traces = reporter.translate_to_stackdriver(trace)

        trace['projectId'] = project_id
        expected_traces = {'traces': [trace]}

        self.assertEqual(traces, expected_traces)
