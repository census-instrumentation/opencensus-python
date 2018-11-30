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

import unittest
import mock
import threading

from opencensus.trace import execution_context


class Test__get_opencensus_attr(unittest.TestCase):
    def tearDown(self):
        execution_context.clear()

    def test_no_attrs(self):
        key = 'key'

        result = execution_context.get_opencensus_attr(key)

        self.assertIsNone(result)

    def test_has_attrs(self):
        key = 'key'
        value = 'value'

        execution_context.set_opencensus_attr(key, value)

        result = execution_context.get_opencensus_attr(key)

        self.assertEqual(result, value)

    def test_get_and_set_full_context(self):
        mock_tracer_get = mock.Mock()
        mock_span_get = mock.Mock()
        execution_context.set_opencensus_tracer(mock_tracer_get)
        execution_context.set_current_span(mock_span_get)

        execution_context.set_opencensus_attr("test", "test_value")

        tracer, span, attrs = execution_context.get_opencensus_full_context()

        self.assertEqual(mock_tracer_get, tracer)
        self.assertEqual(mock_span_get, span)
        self.assertEqual({"test": "test_value"}, attrs)

        mock_tracer_set = mock.Mock()
        mock_span_set = mock.Mock()

        execution_context.set_opencensus_full_context(mock_tracer_set,
                                                      mock_span_set, None)
        self.assertEqual(mock_tracer_set,
                         execution_context.get_opencensus_tracer())
        self.assertEqual(mock_span_set, execution_context.get_current_span())
        self.assertEqual({}, execution_context.get_opencensus_attrs())

        execution_context.set_opencensus_full_context(
            mock_tracer_set, mock_span_set, {"test": "test_value"})
        self.assertEqual("test_value",
                         execution_context.get_opencensus_attr("test"))

    def test_clean_tracer(self):
        mock_tracer = mock.Mock()
        some_value = mock.Mock()
        execution_context.set_opencensus_tracer(mock_tracer)

        thread_local = threading.local()
        setattr(thread_local, 'random_non_oc_attr', some_value)

        execution_context.clean()

        self.assertNotEqual(mock_tracer,
                            execution_context.get_opencensus_tracer())
        self.assertEqual(some_value, getattr(thread_local,
                                             'random_non_oc_attr'))

    def test_clean_span(self):
        mock_span = mock.Mock()
        some_value = mock.Mock()
        execution_context.set_current_span(mock_span)

        thread_local = threading.local()
        setattr(thread_local, 'random_non_oc_attr', some_value)

        execution_context.clean()

        self.assertNotEqual(mock_span, execution_context.get_current_span())
        self.assertEqual(some_value, getattr(thread_local,
                                             'random_non_oc_attr'))
