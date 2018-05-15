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
        tag_values = view_data.get_tag_values(tags, columns)
        self.assertEqual(['testVal1'], tag_values)

        tags = {'testTag1': 'testVal1'}
        columns = ['testTag2']
        tag_values = view_data.get_tag_values(tags, columns)
        self.assertEqual([None], tag_values)

    def test_record(self):
        view = mock.Mock()
        view.columns = ['key1']
        view.aggregation = mock.Mock()
        start_time = datetime.utcnow()
        end_time = datetime.utcnow()
        view_data = view_data_module.ViewData(view=view,
                                              start_time=start_time,
                                              end_time=end_time)

        context = {'key1': 'val1', 'key2': 'val2'}
        time = datetime.utcnow().isoformat() + 'Z'
        value = 1
        self.assertEqual({}, view_data.tag_value_aggregation_map)

        view_data.record(context=context, value=value, timestamp=time)
        tag_values = view_data.get_tag_values(
            tags=view_data.get_tag_map(context=context), columns=view.columns)
        tuple_vals = tuple(tag_values)
        self.assertEqual(['val1'], tag_values)
        self.assertIsNotNone(view_data.tag_value_aggregation_map)

        self.assertTrue('val1' in view_data.tag_value_aggregation_map)
        self.assertTrue('val1' in tag_values)
        self.assertIsNotNone(view_data.tag_value_aggregation_map['val1'])
        self.assertIsNotNone(view_data.tag_value_aggregation_map.get(
            'val1').add(value))

        view_data.record(context=context, value=value, timestamp=time)
        tag_values.append('val2')
        self.assertFalse('val2' in view_data.tag_value_aggregation_map)
        view_data.tag_value_aggregation_map['val2'] = view.aggregation
        self.assertEqual(view_data.tag_value_aggregation_map.get('val2'),
                         view_data.view.aggregation)
        self.assertIsNotNone(view_data.tag_value_aggregation_map.get(
            'val2').add(value))
