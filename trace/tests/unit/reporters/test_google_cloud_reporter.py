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


class TestGoogleCloudReporter(unittest.TestCase):

    @mock.patch('google.cloud.client._determine_default_project')
    def test_constructor_default(self, default_mock):
        default_mock.return_value = 'foo'
        reporter = google_cloud_reporter.GoogleCloudReporter()

        self.assertEqual(reporter.project_id, reporter.client.project)

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
        traces = {'traces': [trace]}

        client = mock.Mock()
        project_id = 'PROJECT'
        client.project = project_id

        reporter = google_cloud_reporter.GoogleCloudReporter(
            client=client,
            project_id=project_id)

        reporter.report(traces)

        self.assertEqual(traces['traces'][0]['projectId'], project_id)
        self.assertTrue(client.patch_traces.called)


class Client(object):
    def __init__(self):
        self.project = 'PROJECT'
