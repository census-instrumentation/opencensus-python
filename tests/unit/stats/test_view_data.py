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

from datetime import datetime
import mock
import unittest

from opencensus.common import utils
from opencensus.stats import aggregation as aggregation_module
from opencensus.stats import measure as measure_module
from opencensus.stats import view_data as view_data_module
from opencensus.stats import view as view_module


class TestViewData(unittest.TestCase):
    def test_constructor(self):
        view = mock.Mock()
        start_time = datetime.utcnow()
        end_time = datetime.utcnow()
        view_data = view_data_module.ViewData(
            view=view, start_time=start_time, end_time=end_time)

        self.assertEqual(view, view_data.view)
        self.assertEqual(start_time, view_data.start_time)
        self.assertEqual(end_time, view_data.end_time)
        self.assertEqual({}, view_data.tag_value_aggregation_data_map)

    def test_start(self):
        view = mock.Mock()
        start_time = mock.Mock()
        end_time = datetime.utcnow()
        view_data = view_data_module.ViewData(
            view=view, start_time=start_time, end_time=end_time)
        view_data.start()

        self.assertIsNotNone(view_data.start_time)

    def test_end(self):
        view = mock.Mock()
        start_time = datetime.utcnow()
        end_time = mock.Mock()
        view_data = view_data_module.ViewData(
            view=view, start_time=start_time, end_time=end_time)
        view_data.end()

        self.assertIsNotNone(view_data.end_time)

    def test_get_tag_values(self):
        view = mock.Mock()
        start_time = datetime.utcnow()
        end_time = datetime.utcnow()
        view_data = view_data_module.ViewData(
            view=view, start_time=start_time, end_time=end_time)

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
        view_data = view_data_module.ViewData(
            view=view, start_time=start_time, end_time=end_time)

        context = mock.Mock()
        context.map = {'key1': 'val1', 'key2': 'val2'}
        time = utils.to_iso_str()
        value = 1
        self.assertEqual({}, view_data.tag_value_aggregation_data_map)

        view_data.record(context=context, value=value, timestamp=time)
        tag_values = view_data.get_tag_values(
            tags=context.map, columns=view.columns)
        tuple_vals = tuple(tag_values)
        self.assertEqual(['val1'], tag_values)
        self.assertIsNotNone(view_data.tag_value_aggregation_data_map)

        self.assertTrue(tuple_vals in view_data.tag_value_aggregation_data_map)
        self.assertIsNotNone(
            view_data.tag_value_aggregation_data_map[tuple_vals])
        self.assertIsNotNone(
            view_data.tag_value_aggregation_data_map.get(tuple_vals).add(
                value))

        view_data.record(context=context, value=value, timestamp=time)
        tag_values.append('val2')
        tuple_vals_2 = tuple(['val2'])
        self.assertFalse(
            tuple_vals_2 in view_data.tag_value_aggregation_data_map)
        view_data.tag_value_aggregation_data_map[
            tuple_vals_2] = view.aggregation
        self.assertEqual(
            view_data.tag_value_aggregation_data_map.get(tuple_vals_2),
            view_data.view.aggregation)
        self.assertIsNotNone(
            view_data.tag_value_aggregation_data_map.get(tuple_vals_2).add(
                value))

    def test_record_with_attachment(self):
        boundaries = [1, 2, 3]
        distribution = {1: "test"}
        distribution_aggregation = aggregation_module.DistributionAggregation(
            boundaries=boundaries, distribution=distribution)
        name = "testName"
        description = "testMeasure"
        unit = "testUnit"

        measure = measure_module.MeasureInt(
            name=name, description=description, unit=unit)

        description = "testMeasure"
        columns = ["key1", "key2"]

        view = view_module.View(
            name=name,
            description=description,
            columns=columns,
            measure=measure,
            aggregation=distribution_aggregation)

        start_time = datetime.utcnow()
        attachments = {"One": "one", "Two": "two"}
        end_time = datetime.utcnow()
        view_data = view_data_module.ViewData(
            view=view, start_time=start_time, end_time=end_time)
        context = mock.Mock
        context.map = {'key1': 'val1', 'key2': 'val2'}
        time = utils.to_iso_str()
        value = 1

        view_data.record(
            context=context,
            value=value,
            timestamp=time,
            attachments=attachments)
        tag_values = view_data.get_tag_values(
            tags=context.map, columns=view.columns)
        tuple_vals = tuple(tag_values)

        self.assertEqual(['val1', 'val2'], tag_values)
        self.assertIsNotNone(view_data.tag_value_aggregation_data_map)
        self.assertTrue(tuple_vals in view_data.tag_value_aggregation_data_map)
        self.assertIsNotNone(
            view_data.tag_value_aggregation_data_map[tuple_vals])
        self.assertEqual(
            attachments, view_data.tag_value_aggregation_data_map[tuple_vals].
            exemplars[1].attachments)

    def test_record_with_attachment_no_histogram(self):
        boundaries = None
        distribution = {1: "test"}
        distribution_aggregation = aggregation_module.DistributionAggregation(
            boundaries=boundaries, distribution=distribution)
        name = "testName"
        description = "testMeasure"
        unit = "testUnit"

        measure = measure_module.MeasureInt(
            name=name, description=description, unit=unit)

        description = "testMeasure"
        columns = ["key1", "key2"]

        view = view_module.View(
            name=name,
            description=description,
            columns=columns,
            measure=measure,
            aggregation=distribution_aggregation)

        start_time = datetime.utcnow()
        attachments = {"One": "one", "Two": "two"}
        end_time = datetime.utcnow()
        view_data = view_data_module.ViewData(
            view=view, start_time=start_time, end_time=end_time)
        context = mock.Mock
        context.map = {'key1': 'val1', 'key2': 'val2'}
        time = utils.to_iso_str()
        value = 1
        view_data.record(
            context=context,
            value=value,
            timestamp=time,
            attachments=attachments)
        tag_values = view_data.get_tag_values(
            tags=context.map, columns=view.columns)
        tuple_vals = tuple(tag_values)

        self.assertEqual(['val1', 'val2'], tag_values)
        self.assertIsNotNone(view_data.tag_value_aggregation_data_map)
        self.assertTrue(tuple_vals in view_data.tag_value_aggregation_data_map)
        self.assertIsNotNone(
            view_data.tag_value_aggregation_data_map[tuple_vals])
        self.assertIsNone(
            view_data.tag_value_aggregation_data_map[tuple_vals].exemplars)

    def test_record_with_multi_keys(self):
        measure = mock.Mock()
        sum_aggregation = aggregation_module.SumAggregation()
        view = view_module.View("test_view", "description", ['key1', 'key2'],
                                measure, sum_aggregation)
        start_time = datetime.utcnow()
        end_time = datetime.utcnow()
        view_data = view_data_module.ViewData(
            view=view, start_time=start_time, end_time=end_time)
        context = mock.Mock()
        context.map = {'key1': 'val1', 'key2': 'val2'}
        time = utils.to_iso_str()
        value = 1
        self.assertEqual({}, view_data.tag_value_aggregation_data_map)

        view_data.record(
            context=context, value=value, timestamp=time, attachments=None)
        tag_values = view_data.get_tag_values(
            tags=context.map, columns=view.columns)
        tuple_vals = tuple(tag_values)
        self.assertEqual(['val1', 'val2'], tag_values)
        self.assertIsNotNone(view_data.tag_value_aggregation_data_map)
        self.assertTrue(tuple_vals in view_data.tag_value_aggregation_data_map)
        self.assertIsNotNone(
            view_data.tag_value_aggregation_data_map[tuple_vals])
        sum_data = view_data.tag_value_aggregation_data_map.get(tuple_vals)
        self.assertEqual(1, sum_data.sum_data)

        context_2 = mock.Mock()
        context_2.map = {'key1': 'val3', 'key2': 'val2'}
        time_2 = utils.to_iso_str()
        value_2 = 2
        view_data.record(
            context=context_2,
            value=value_2,
            timestamp=time_2,
            attachments=None)
        tag_values_2 = view_data.get_tag_values(
            tags=context_2.map, columns=view.columns)
        tuple_vals_2 = tuple(tag_values_2)
        self.assertEqual(['val3', 'val2'], tag_values_2)
        self.assertTrue(
            tuple_vals_2 in view_data.tag_value_aggregation_data_map)
        sum_data_2 = view_data.tag_value_aggregation_data_map.get(tuple_vals_2)
        self.assertEqual(2, sum_data_2.sum_data)

        time_3 = utils.to_iso_str()
        value_3 = 3
        # Use the same context {'key1': 'val1', 'key2': 'val2'}.
        # Record to entry [(val1, val2), sum=1].
        view_data.record(
            context=context, value=value_3, timestamp=time_3, attachments=None)
        self.assertEqual(4, sum_data.sum_data)
        # The other entry should remain unchanged.
        self.assertEqual(2, sum_data_2.sum_data)

    def test_record_with_missing_key_in_context(self):
        measure = mock.Mock()
        sum_aggregation = aggregation_module.SumAggregation()
        view = view_module.View("test_view", "description", ['key1', 'key2'],
                                measure, sum_aggregation)
        start_time = datetime.utcnow()
        end_time = datetime.utcnow()
        view_data = view_data_module.ViewData(
            view=view, start_time=start_time, end_time=end_time)
        context = mock.Mock()
        context.map = {
            'key1': 'val1',
            'key3': 'val3'
        }  # key2 is not in the context.
        time = utils.to_iso_str()
        value = 4
        view_data.record(
            context=context, value=value, timestamp=time, attachments=None)
        tag_values = view_data.get_tag_values(
            tags=context.map, columns=view.columns)
        tuple_vals = tuple(tag_values)
        self.assertEqual(['val1', None], tag_values)
        self.assertTrue(tuple_vals in view_data.tag_value_aggregation_data_map)
        sum_data = view_data.tag_value_aggregation_data_map.get(tuple_vals)
        self.assertEqual(4, sum_data.sum_data)

    def test_record_with_none_context(self):
        measure = mock.Mock()
        sum_aggregation = aggregation_module.SumAggregation()
        view = view_module.View("test_view", "description", ['key1', 'key2'],
                                measure, sum_aggregation)
        start_time = datetime.utcnow()
        end_time = datetime.utcnow()
        view_data = view_data_module.ViewData(
            view=view, start_time=start_time, end_time=end_time)
        time = utils.to_iso_str()
        value = 4
        view_data.record(
            context=None, value=value, timestamp=time, attachments=None)
        tag_values = view_data.get_tag_values(
            tags={}, columns=view.columns)
        tuple_vals = tuple(tag_values)
        self.assertEqual([None, None], tag_values)
        self.assertTrue(tuple_vals in view_data.tag_value_aggregation_data_map)
        sum_data = view_data.tag_value_aggregation_data_map.get(tuple_vals)
        self.assertEqual(4, sum_data.sum_data)
