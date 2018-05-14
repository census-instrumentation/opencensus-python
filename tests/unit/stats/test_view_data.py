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

    def test_constructor(self):
        view = mock.Mock()
        start_time = datetime.utcnow()
        end_time = datetime.utcnow()
        view_data = view_data_module.ViewData(view=view, start_time=start_time, end_time=end_time)

        self.assertEqual(view, view_data.view)
        self.assertEqual(start_time, view_data.start_time)
        self.assertEqual(end_time, view_data.end_time)
        self.assertEqual({}, view_data.tag_value_aggregation_map)

    def test_start(self):
        view = mock.Mock()
        start_time = mock.Mock()
        end_time = datetime.utcnow()
        view_data = view_data_module.ViewData(view=view,
                                              start_time=start_time,
                                              end_time=end_time)
        view_data.start()

        self.assertIsNotNone(view_data.start_time)

    def test_end(self):
        view = mock.Mock()
        start_time = datetime.utcnow()
        end_time = mock.Mock()
        view_data = view_data_module.ViewData(view=view,
                                              start_time=start_time,
                                              end_time=end_time)
        view_data.end()

        self.assertIsNotNone(view_data.end_time)

    def test_get_tag_map(self):
        view = mock.Mock()
        start_time = datetime.utcnow()
        end_time = datetime.utcnow()
        view_data = view_data_module.ViewData(view=view,
                                              start_time=start_time,
                                              end_time=end_time)
        test_context_1 = {'key1': 'val1'}
        context_map_1 = view_data.get_tag_map(context=test_context_1)
        self.assertEqual(test_context_1, view_data.tag_map)
        self.assertEqual(test_context_1, context_map_1)

        test_context_2 = {'key1': 'val2'}
        context_map_2 = view_data.get_tag_map(context=test_context_2)
        self.assertEqual(test_context_2, context_map_2)

        test_context_3 = {}
        context_map_3 = view_data.get_tag_map(context=test_context_3)
        self.assertEqual({'key1': 'val2'}, context_map_3)

    def test_get_tag_values(self):
        view = mock.Mock()
        start_time = datetime.utcnow()
        end_time = datetime.utcnow()
        view_data = view_data_module.ViewData(view=view,
                                              start_time=start_time,
                                              end_time=end_time)

        tags = {'testTag1': 'testVal1'}
        columns = ['testTag1']
        view_data.get_tag_values(tags, columns)

        self.assertEqual(['testVal1'], view_data.get_tag_values(tags, columns))

    def test_record(self):
        view = mock.Mock()
        view.columns = ['testKey']
        start_time = datetime.utcnow()
        end_time = datetime.utcnow()
        view_data = view_data_module.ViewData(view=view,
                                              start_time=start_time,
                                              end_time=end_time)

        context = {'key1': 'val2'}
        time = datetime.utcnow().isoformat() + 'Z'
        value = 1
        view_data.record(context, value, time)
        self.assertIsNotNone(view_data.tag_value_aggregation_map)
