# Copyright 2018, OpenCensus Authors
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
from opencensus.trace.base_span import BaseSpan


class TestBaseSpan(unittest.TestCase):
    def test_span_abstract(self):
        span = BaseSpan()

        with self.assertRaises(NotImplementedError):
            span.span('root_span')

    def test_children_abstract(self):
        span = BaseSpan()

        with self.assertRaises(NotImplementedError):
            span.children

    def test_create_abstract(self):
        with self.assertRaises(NotImplementedError):

            @BaseSpan.on_create
            def callback(span):
                pass

    def test_start_abstract(self):
        span = BaseSpan()

        with self.assertRaises(NotImplementedError):
            span.start()

    def test_finish_abstract(self):
        span = BaseSpan()

        with self.assertRaises(NotImplementedError):
            span.finish()

    def test_add_attribute_abstract(self):
        span = BaseSpan()

        with self.assertRaises(NotImplementedError):
            span.add_attribute("key", "value")

    def test_add_annotation_abstract(self):
        span = BaseSpan()

        with self.assertRaises(NotImplementedError):
            span.add_annotation("desc")

    def test_add_message_event_abstract(self):
        span = BaseSpan()

        with self.assertRaises(NotImplementedError):
            span.add_message_event(None)

    def test_add_link_abstract(self):
        span = BaseSpan()

        with self.assertRaises(NotImplementedError):
            span.add_link(None)

    def test_set_status_abstract(self):
        span = BaseSpan()

        with self.assertRaises(NotImplementedError):
            span.set_status(None)

    def test_iter_abstract(self):
        span = BaseSpan()

        with self.assertRaises(NotImplementedError):
            list(iter(span))

    @mock.patch.object(BaseSpan, '__exit__')
    @mock.patch.object(BaseSpan, '__enter__')
    def test_context_manager_called(self, mock_enter, mock_exit):
        span = BaseSpan()
        with span:
            pass
        self.assertTrue(mock_enter.called)
        self.assertTrue(mock_exit.called)

    def test_context_manager_methods(self):
        span = BaseSpan()
        with self.assertRaises(NotImplementedError):
            span.__enter__()

        with self.assertRaises(NotImplementedError):
            span.__exit__(None, None, None)
