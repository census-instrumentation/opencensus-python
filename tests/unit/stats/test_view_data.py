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
from datetime import datetime
from opencensus.stats import view_data as view_data_module


class TestViewData(unittest.TestCase):

    def test_constructor_defaults(self):
        view = mock.Mock()
        start_time = datetime.utcnow()
        end_time = datetime.utcnow()
        view_data = view_data_module.ViewData(view=view, start_time=start_time, end_time=end_time)

        self.assertEqual(view, view_data.view)
        self.assertEqual(start_time, view_data.start_time)
        self.assertEqual(end_time, view_data.end_time)
        self.assertEqual({}, view_data.rows)

    def test_constructor_explicit(self):
        view = mock.Mock()
        start_time = datetime.utcnow()
        end_time = datetime.utcnow()
        rows = mock.Mock()
        view_data = view_data_module.ViewData(view=view, start_time=start_time, end_time=end_time, rows=rows)

        self.assertEqual(view, view_data.view)
        self.assertEqual(start_time, view_data.start_time)
        self.assertEqual(end_time, view_data.end_time)
        self.assertEqual(rows, view_data.rows)

    def test_start(self):
        view = mock.Mock()
        start_time = mock.Mock()
        end_time = datetime.utcnow()
        rows = mock.Mock()
        view_data = view_data_module.ViewData(view=view, start_time=start_time, end_time=end_time, rows=rows)
        view_data.start()

        self.assertIsNotNone(view_data.start_time)

    def test_end(self):
        view = mock.Mock()
        start_time = datetime.utcnow()
        end_time = mock.Mock()
        rows = mock.Mock()
        view_data = view_data_module.ViewData(view=view, start_time=start_time, end_time=end_time, rows=rows)
        view_data.end()

        self.assertIsNotNone(view_data.end_time)

    def test_get_tag_map(self):
        view = mock.Mock()
        start_time = datetime.utcnow()
        end_time = datetime.utcnow()
        rows = mock.Mock()
        context = {'key1': 'val2'}
        context_2 = {'key1': 'val1'}
        view_data = view_data_module.ViewData(view=view, start_time=start_time, end_time=end_time, rows=rows)
        view_data.get_tag_map(context=context)
        view_data.get_tag_map(context=context_2)

        self.assertEqual(context, view_data.get_tag_map(context=context))
        self.assertEqual(context_2, view_data.get_tag_map(context=context_2))

    def test_get_tag_values(self):
        view = mock.Mock()
        start_time = datetime.utcnow()
        end_time = datetime.utcnow()
        rows = mock.Mock()
        view_data = view_data_module.ViewData(view=view, start_time=start_time, end_time=end_time, rows=rows)

        tags = {'testTag1': 'testVal1'}
        columns = ['testTag1']
        view_data.get_tag_values(tags, columns)

        self.assertEqual(['testVal1'], view_data.get_tag_values(tags, columns))

    def test_record(self):
        view = mock.Mock()
        view.columns = ['testKey']
        start_time = datetime.utcnow()
        end_time = datetime.utcnow()
        rows = mock.Mock()
        view_data = view_data_module.ViewData(view=view, start_time=start_time, end_time=end_time, rows=rows)

        context = {'key1': 'val2'}
        time = datetime.utcnow().isoformat() + 'Z'
        value = 1
        view_data.record(context, value, time)
        self.assertIsNotNone(view_data.tag_value_aggregation_map)

