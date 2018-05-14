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
from opencensus.stats import measurement_map as measurement_map_module
from opencensus.stats.measure_to_view_map import MeasureToViewMap


class TestMeasurementMap(unittest.TestCase):

    def test_constructor_explicit(self):
        measure_to_view_map = {'testMeasure1': 'testVal1'}
        measurement_map = measurement_map_module.MeasurementMap(
            measure_to_view_map=measure_to_view_map)

        self.assertEqual(measure_to_view_map,
                         measurement_map.measure_to_view_map)
        self.assertEqual({}, measurement_map.measurement_map)

    def test_measure_int_put(self):
        measure_to_view_map = mock.Mock()
        test_key = 'testKey'
        test_value = 1
        measurement_map = measurement_map_module.MeasurementMap(
            measure_to_view_map=measure_to_view_map)
        measurement_map.measure_int_put(test_key, test_value)

        self.assertEqual({'testKey': 1}, measurement_map.measurement_map)

    def test_measure_float_put(self):
        measure_to_view_map = mock.Mock()
        test_key = 'testKey'
        test_value = 1.0
        measurement_map = measurement_map_module.MeasurementMap(
            measure_to_view_map=measure_to_view_map)
        measurement_map.measure_float_put(test_key, test_value)

        self.assertEqual({'testKey': 1.0}, measurement_map.measurement_map)

    def test_record(self):
        measure_to_view_map = mock.Mock()
        measurement_map = measurement_map_module.MeasurementMap(
            measure_to_view_map=measure_to_view_map)

        tags = {'testtag1': 'testtag1val'}
        measurement_map.record(tag_map_tags=tags)
        self.assertTrue(measure_to_view_map.MeasureToViewMap.record.called)
