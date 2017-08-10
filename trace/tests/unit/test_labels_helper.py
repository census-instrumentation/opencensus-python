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

from opencensus.trace.labels_helper import LabelsHelper

import unittest

import mock

class TestLabelsHelper(unittest.TestCase):

    def test_constructor(self):
        tracer = mock.Mock()
        reporter = mock.Mock()
        tracer.reporter = reporter

        labels_helper = LabelsHelper(tracer=tracer)

        self.assertEqual(labels_helper.tracer, tracer)
        self.assertEqual(labels_helper.reporter, reporter)

    def test_set_labels_gae(self):
        from opencensus.trace.labels_helper import _APPENGINE_FLEXIBLE_ENV_VM
        from opencensus.trace.labels_helper import _APPENGINE_FLEXIBLE_ENV_FLEX
        from opencensus.trace.labels_helper import _GAE_PROJECT_ENV
        from opencensus.trace.labels_helper import _GAE_SERVICE_ENV
        from opencensus.trace.labels_helper import _GAE_VERSION_ENV
        from opencensus.trace.labels_helper import GAELabels

        import os

        tracer = Tracer()
        cur_trace = mock.Mock()
        span = Span()
        cur_trace.spans = [span]
        tracer.cur_trace = cur_trace

        labels_helper = LabelsHelper(tracer)

        expected_labels = {
            GAELabels.GAE_PROJECT: 'project',
            GAELabels.GAE_SERVICE: 'service',
            GAELabels.GAE_VERSION: 'version',
        }

        with mock.patch.dict(
                os.environ,
                {_APPENGINE_FLEXIBLE_ENV_VM: 'vm',
                 _APPENGINE_FLEXIBLE_ENV_FLEX: 'flex',
                 _GAE_PROJECT_ENV: 'project',
                 _GAE_SERVICE_ENV: 'service',
                 _GAE_VERSION_ENV: 'version'}):
            labels_helper.set_labels()
            print(tracer.cur_trace.spans[0].labels)

        self.assertEqual(tracer.cur_trace.spans[0].labels, expected_labels)

    def test_set_labels_stackdriver(self):
        # TODO; Add assertions when implement set_stackdriver_labels()
        from opencensus.trace.reporters import google_cloud_reporter

        reporter = mock.Mock(spec=google_cloud_reporter.GoogleCloudReporter)
        tracer = mock.Mock()
        tracer.reporter = reporter

        labels_helper = LabelsHelper(tracer)

        labels_helper.set_labels()


class Tracer(object):
    def __init__(self):
        self.reporter = None
        self.cur_trace = None

    def add_label_to_spans(self, label_key, label_value):
        for span in self.cur_trace.spans:
            span.add_label(label_key, label_value)


class Span(object):
    def __init__(self):
        self.labels = {}

    def add_label(self, label_key, label_value):
        self.labels[label_key] = label_value
