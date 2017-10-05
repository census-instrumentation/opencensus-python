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

from opencensus.trace.labels_helper import LabelsHelper

import unittest

import mock

class TestLabelsHelper(unittest.TestCase):

    def test_constructor(self):
        tracer = mock.Mock()

        labels_helper = LabelsHelper(tracer=tracer)

        self.assertEqual(labels_helper.tracer, tracer)

    def test_set_labels_gae(self):
        from opencensus.trace.labels_helper import _APPENGINE_FLEXIBLE_ENV_VM
        from opencensus.trace.labels_helper import _APPENGINE_FLEXIBLE_ENV_FLEX
        from opencensus.trace.labels_helper import GAE_LABELS

        import os

        tracer = Tracer()
        cur_trace = mock.Mock()
        span = Span()
        cur_trace.spans = [span]
        tracer.cur_trace = cur_trace

        labels_helper = LabelsHelper(tracer)

        expected_labels = {
            GAE_LABELS['GAE_FLEX_PROJECT']: 'project',
            GAE_LABELS['GAE_FLEX_SERVICE']: 'service',
            GAE_LABELS['GAE_FLEX_VERSION']: 'version',
        }

        with mock.patch.dict(
                os.environ,
                {_APPENGINE_FLEXIBLE_ENV_VM: 'vm',
                 _APPENGINE_FLEXIBLE_ENV_FLEX: 'flex',
                 'GAE_FLEX_PROJECT': 'project',
                 'GAE_FLEX_SERVICE': 'service',
                 'GAE_FLEX_VERSION': 'version'}):
            labels_helper.set_labels()
            print(tracer.cur_trace.spans[0].labels)

        self.assertEqual(tracer.cur_trace.spans[0].labels, expected_labels)


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
