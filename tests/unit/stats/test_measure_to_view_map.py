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

from opencensus.stats import measure_to_view_map as measure_to_view_map_module
from opencensus.stats.aggregation import CountAggregation
from opencensus.stats.measure import BaseMeasure
from opencensus.stats.measure import MeasureInt
from opencensus.stats.view import View
from opencensus.stats.view_data import ViewData
from opencensus.tags import tag_key as tag_key_module


METHOD_KEY = tag_key_module.TagKey("method")
REQUEST_COUNT_MEASURE = MeasureInt(
    "request_count", "number of requests", "1")
REQUEST_COUNT_VIEW_NAME = "request_count_view"
COUNT = CountAggregation()
REQUEST_COUNT_VIEW = View(
    REQUEST_COUNT_VIEW_NAME,
    "number of requests broken down by methods",
    [METHOD_KEY], REQUEST_COUNT_MEASURE, COUNT)


class TestMeasureToViewMap(unittest.TestCase):
    @staticmethod
    def _get_target_class():
        return measure_to_view_map_module.MeasureToViewMap

    def _make_one(self, *args, **kw):
        return self._get_target_class()(*args, **kw)

    def test_constructor(self):
        measure_to_view_map = measure_to_view_map_module.MeasureToViewMap()

        self.assertEqual({},
                         measure_to_view_map._measure_to_view_data_list_map)
        self.assertEqual({}, measure_to_view_map._registered_views)
        self.assertEqual({}, measure_to_view_map._registered_measures)
        self.assertEqual(set(), measure_to_view_map.exported_views)

    def test_get_view(self):
        name = "testView"
        description = "testDescription"
        columns = mock.Mock()
        measure = mock.Mock()
        aggregation = mock.Mock()
        view = View(
            name=name,
            description=description,
            columns=columns,
            measure=measure,
            aggregation=aggregation)
        timestamp = mock.Mock()
        measure_to_view_map = measure_to_view_map_module.MeasureToViewMap()

        measure_to_view_map._registered_views = {}
        no_registered_views = measure_to_view_map.get_view(
            view_name=name, timestamp=timestamp)
        self.assertEqual(None, no_registered_views)

        measure_to_view_map._registered_views = {name: view}
        measure_to_view_map._measure_to_view_data_list_map = {
            view.measure.name:
            [ViewData(view=view, start_time=timestamp, end_time=timestamp)]
        }

        view_data = measure_to_view_map.get_view(
            view_name=name, timestamp=timestamp)
        self.assertIsNotNone(view_data)

        measure_to_view_map._measure_to_view_data_list_map = {}
        view_data = measure_to_view_map.get_view(
            view_name=name, timestamp=timestamp)
        self.assertIsNone(view_data)

        measure_to_view_map._measure_to_view_data_list_map = {
            view.measure.name: [
                ViewData(
                    view=mock.Mock(), start_time=timestamp, end_time=timestamp)
            ]
        }
        view_data = measure_to_view_map.get_view(
            view_name=name, timestamp=timestamp)
        self.assertIsNone(view_data)

    def test_filter_exported_views(self):
        test_view_1_name = "testView1"
        description = "testDescription"
        columns = mock.Mock()
        measure = mock.Mock()
        aggregation = mock.Mock()
        test_view_1 = View(
            name=test_view_1_name,
            description=description,
            columns=columns,
            measure=measure,
            aggregation=aggregation)

        test_view_2_name = "testView2"
        test_view_2 = View(
            name=test_view_2_name,
            description=description,
            columns=columns,
            measure=measure,
            aggregation=aggregation)
        all_the_views = {test_view_1, test_view_2}
        measure_to_view_map = measure_to_view_map_module.MeasureToViewMap()
        views = measure_to_view_map.filter_exported_views(
            all_views=all_the_views)
        self.assertEqual(views, all_the_views)

    def test_register_view(self):
        name = "testView"
        description = "testDescription"
        columns = mock.Mock()
        measure = MeasureInt("measure", "description", "1")
        aggregation = mock.Mock()
        view = View(
            name=name,
            description=description,
            columns=columns,
            measure=measure,
            aggregation=aggregation)
        timestamp = mock.Mock()
        measure_to_view_map = measure_to_view_map_module.MeasureToViewMap()

        measure_to_view_map._registered_views = {}
        measure_to_view_map._registered_measures = {}
        measure_to_view_map.register_view(view=view, timestamp=timestamp)
        self.assertIsNone(measure_to_view_map.exported_views)
        self.assertEqual(measure_to_view_map._registered_views[view.name],
                         view)
        self.assertEqual(
            measure_to_view_map._registered_measures[measure.name], measure)
        self.assertIsNotNone(measure_to_view_map.
                             _measure_to_view_data_list_map[view.measure.name])

        # Registers a view with an existing measure.
        view2 = View(
            name="testView2",
            description=description,
            columns=columns,
            measure=measure,
            aggregation=aggregation)
        test_with_registered_measures = measure_to_view_map.register_view(
            view=view2, timestamp=timestamp)
        self.assertIsNone(test_with_registered_measures)
        self.assertEqual(
            measure_to_view_map._registered_measures[measure.name], measure)

        # Registers a view with a measure that has the same name as an existing
        # measure, but with different schema. measure2 and view3 should be
        # ignored.
        measure2 = MeasureInt("measure", "another measure", "ms")
        view3 = View(
            name="testView3",
            description=description,
            columns=columns,
            measure=measure2,
            aggregation=aggregation)
        test_with_registered_measures = measure_to_view_map.register_view(
            view=view3, timestamp=timestamp)
        self.assertIsNone(test_with_registered_measures)
        self.assertEqual(
            measure_to_view_map._registered_measures[measure2.name], measure)

        measure_to_view_map._registered_measures = {measure.name: None}
        self.assertIsNone(
            measure_to_view_map._registered_measures.get(measure.name))
        measure_to_view_map.register_view(view=view, timestamp=timestamp)
        # view is already registered, measure will not be registered again.
        self.assertIsNone(
            measure_to_view_map._registered_measures.get(measure.name))
        self.assertIsNotNone(measure_to_view_map.
                             _measure_to_view_data_list_map[view.measure.name])

        measure_to_view_map._registered_views = {name: view}
        test_result_1 = measure_to_view_map.register_view(
            view=view, timestamp=timestamp)
        self.assertIsNone(test_result_1)
        self.assertIsNotNone(measure_to_view_map.
                             _measure_to_view_data_list_map[view.measure.name])

    def test_register_view_with_exporter(self):
        exporter = mock.Mock()
        name = "testView"
        description = "testDescription"
        columns = mock.Mock()
        measure = MeasureInt("measure", "description", "1")
        aggregation = mock.Mock()
        view = View(
            name=name,
            description=description,
            columns=columns,
            measure=measure,
            aggregation=aggregation)
        timestamp = mock.Mock()
        measure_to_view_map = measure_to_view_map_module.MeasureToViewMap()
        measure_to_view_map.exporters.append(exporter)
        measure_to_view_map._registered_views = {}
        measure_to_view_map._registered_measures = {}
        measure_to_view_map.register_view(view=view, timestamp=timestamp)
        self.assertIsNone(measure_to_view_map.exported_views)
        self.assertEqual(measure_to_view_map._registered_views[view.name],
                         view)
        self.assertEqual(
            measure_to_view_map._registered_measures[measure.name], measure)
        self.assertIsNotNone(measure_to_view_map.
                             _measure_to_view_data_list_map[view.measure.name])

    def test_record(self):
        measure_name = "test_measure"
        measure_description = "test_description"
        measure = BaseMeasure(
            name=measure_name, description=measure_description)

        view_name = "test_view"
        view_description = "test_description"
        view_columns = ["testTag1", "testColumn2"]
        view_measure = measure
        view_aggregation = mock.Mock()
        View(name=view_name,
             description=view_description,
             columns=view_columns,
             measure=view_measure,
             aggregation=view_aggregation)

        measure_value = 5
        tags = {"testTag1": "testTag1Value"}
        measurement_map = {measure: measure_value}
        timestamp = mock.Mock()

        measure_to_view_map = measure_to_view_map_module.MeasureToViewMap()
        measure_to_view_map._registered_measures = {}
        record = measure_to_view_map.record(
            tags=tags,
            measurement_map=measurement_map,
            timestamp=timestamp,
            attachments=None)
        self.assertNotEqual(
            measure,
            measure_to_view_map._registered_measures.get(measure.name))
        self.assertIsNone(record)

        measure_to_view_map._registered_measures = {measure.name: measure}
        measure_to_view_map._measure_to_view_data_list_map = {}
        record = measure_to_view_map.record(
            tags=tags,
            measurement_map=measurement_map,
            timestamp=timestamp,
            attachments=None)
        self.assertEqual(
            measure,
            measure_to_view_map._registered_measures.get(measure.name))
        self.assertIsNone(record)

        measure_to_view_map._measure_to_view_data_list_map = {
            measure.name: [mock.Mock()]
        }
        measure_to_view_map.record(
            tags=tags,
            measurement_map=measurement_map,
            timestamp=timestamp,
            attachments=None)
        self.assertEqual(
            measure,
            measure_to_view_map._registered_measures.get(measure.name))
        self.assertTrue(
            measure.name in measure_to_view_map._measure_to_view_data_list_map)

        measure_to_view_map._measure_to_view_data_list_map = {
            "testing": [mock.Mock()]
        }
        measure_to_view_map.record(
            tags=tags,
            measurement_map=measurement_map,
            timestamp=timestamp,
            attachments=None)
        self.assertTrue(measure.name not in measure_to_view_map.
                        _measure_to_view_data_list_map)

        measure_to_view_map_mock = mock.Mock()
        measure_to_view_map = measure_to_view_map_mock
        measure_to_view_map._registered_measures = {measure.name: measure}
        measure_to_view_map._measure_to_view_data_list_map = mock.Mock()
        measure_to_view_map.record(
            tags=mock.Mock(), stats=mock.Mock(), timestamp=mock.Mock())
        self.assertEqual(
            measure,
            measure_to_view_map._registered_measures.get(measure.name))
        self.assertIsNotNone(measure_to_view_map.view_datas)
        self.assertTrue(measure_to_view_map_mock.record.called)

        tags = {"testTag1": "testTag1Value"}
        measurement_map = {}
        measure_to_view_map = measure_to_view_map_module.MeasureToViewMap()
        record = measure_to_view_map.record(
            tags=tags,
            measurement_map=measurement_map,
            timestamp=timestamp,
            attachments=None)
        self.assertIsNone(record)

    def test_record_negative_value(self):
        """Check that we warn and drop negative measures at record time."""
        measure = mock.Mock()
        view_data = mock.Mock()
        measure_to_view_map = measure_to_view_map_module.MeasureToViewMap()
        measure_to_view_map._registered_measures = {measure.name: measure}
        measure_to_view_map._measure_to_view_data_list_map = {
            measure.name: [view_data]
        }
        with self.assertRaises(AssertionError):
            measure_to_view_map.record(
                tags=mock.Mock(),
                measurement_map={measure: -1},
                timestamp=mock.Mock())
        view_data.record.assert_not_called()

    def test_record_with_exporter(self):
        exporter = mock.Mock()
        measure_name = "test_measure"
        measure_description = "test_description"
        measure = BaseMeasure(
            name=measure_name, description=measure_description)

        view_name = "test_view"
        view_description = "test_description"
        view_columns = ["testTag1", "testColumn2"]
        view_measure = measure
        view_aggregation = mock.Mock()
        View(
            name=view_name,
            description=view_description,
            columns=view_columns,
            measure=view_measure,
            aggregation=view_aggregation)

        measure_value = 5
        tags = {"testTag1": "testTag1Value"}
        measurement_map = {measure: measure_value}
        timestamp = mock.Mock()

        measure_to_view_map = measure_to_view_map_module.MeasureToViewMap()
        measure_to_view_map.exporters.append(exporter)
        measure_to_view_map._registered_measures = {}
        record = measure_to_view_map.record(
            tags=tags, measurement_map=measurement_map, timestamp=timestamp)
        self.assertNotEqual(
            measure,
            measure_to_view_map._registered_measures.get(measure.name))
        self.assertIsNone(record)

    def test_export(self):
        exporter = mock.Mock()
        view_data = []
        measure_name = "test_measure"
        measure_description = "test_description"
        measure = BaseMeasure(
            name=measure_name, description=measure_description)

        view_name = "test_view"
        view_description = "test_description"
        view_columns = ["testTag1", "testColumn2"]
        view_measure = measure
        view_aggregation = mock.Mock()
        View(
            name=view_name,
            description=view_description,
            columns=view_columns,
            measure=view_measure,
            aggregation=view_aggregation)

        measure_to_view_map = measure_to_view_map_module.MeasureToViewMap()
        measure_to_view_map.exporters.append(exporter)
        measure_to_view_map._registered_measures = {}
        measure_to_view_map.export(view_data)
        self.assertTrue(True)

    def test_export_duplicates_viewdata(self):
        """Check that we copy view data on export."""
        mtvm = measure_to_view_map_module.MeasureToViewMap()

        exporter = mock.Mock()
        mtvm.exporters.append(exporter)

        timestamp1 = mock.Mock()
        timestamp2 = mock.Mock()
        view_data = ViewData(REQUEST_COUNT_VIEW, timestamp1, timestamp2)
        mtvm.export([view_data])
        mtvm.export([view_data])
        self.assertEqual(exporter.export.call_count, 2)

        exported_call1, exported_call2 = exporter.export.call_args_list
        exported_vd1 = exported_call1[0][0][0]
        exported_vd2 = exported_call2[0][0][0]
        self.assertIsNot(exported_vd1, exported_vd2)
        self.assertIsNot(exported_vd1.end_time, view_data.end_time)
        self.assertIsNot(exported_vd2.end_time, view_data.end_time)
