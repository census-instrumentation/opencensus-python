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
from opencensus.tags import execution_context
from opencensus.stats.measure import BaseMeasure
from opencensus.stats.measure import MeasureInt
from opencensus.stats import measure_to_view_map as measure_to_view_map_module
from opencensus.stats.view import View


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

    def test_put_attachment_none_key(self):
        measure_to_view_map = mock.Mock()
        test_key = None
        test_value = 'testValue'
        measurement_map = measurement_map_module.MeasurementMap(
            measure_to_view_map=measure_to_view_map, attachments={})
        with self.assertRaisesRegexp(TypeError, 'attachment key should not be empty and should be a string'):
            measurement_map.measure_put_attachment(test_key, test_value)

    def test_put_attachment_none_value(self):
        measure_to_view_map = mock.Mock()
        test_key = 'testKey'
        test_value = None
        measurement_map = measurement_map_module.MeasurementMap(
            measure_to_view_map=measure_to_view_map, attachments={})
        with self.assertRaisesRegexp(TypeError, 'attachment value should not be empty and should be a string'):
            measurement_map.measure_put_attachment(test_key, test_value)

    def test_put_attachment_int_key(self):
        measure_to_view_map = mock.Mock()
        test_key = 42
        test_value = 'testValue'
        measurement_map = measurement_map_module.MeasurementMap(
            measure_to_view_map=measure_to_view_map, attachments={})
        with self.assertRaisesRegexp(TypeError, 'attachment key should not be empty and should be a string'):
            measurement_map.measure_put_attachment(test_key, test_value)

    def test_put_attachment_int_value(self):
        measure_to_view_map = mock.Mock()
        test_key = 'testKey'
        test_value = 42
        measurement_map = measurement_map_module.MeasurementMap(
            measure_to_view_map=measure_to_view_map, attachments={})
        with self.assertRaisesRegexp(TypeError, 'attachment value should not be empty and should be a string'):
            measurement_map.measure_put_attachment(test_key, test_value)

    def test_put_attachment(self):
        measure_to_view_map = mock.Mock()
        test_key = 'testKey'
        test_value = 'testValue'
        measurement_map = measurement_map_module.MeasurementMap(
            measure_to_view_map=measure_to_view_map, attachments={})
        measurement_map.measure_put_attachment(test_key, test_value)
        self.assertEqual({'testKey': 'testValue'}, measurement_map.attachments)

    def test_put_none_attachment(self):
        measure_to_view_map = mock.Mock()
        test_key = 'testKey'
        test_value = 42
        measurement_map = measurement_map_module.MeasurementMap(
            measure_to_view_map=measure_to_view_map)
        with self.assertRaisesRegexp(TypeError, 'attachments should not be empty'):
            measurement_map.measure_put_attachment(test_key, test_value)

    def test_put_multiple_attachment(self):
        measure_to_view_map = mock.Mock()
        test_key = 'testKey'
        test_value = 'testValue'
        test_value2 = 'testValue2'
        measurement_map = measurement_map_module.MeasurementMap(
            measure_to_view_map=measure_to_view_map, attachments={})
        measurement_map.measure_put_attachment(test_key, test_value)
        measurement_map.measure_put_attachment(test_key, test_value2)
        self.assertEqual({test_key: test_value2}, measurement_map.attachments)

    def test_record_against_explicit_tag_map(self):
        measure_to_view_map = mock.Mock()
        measurement_map = measurement_map_module.MeasurementMap(
            measure_to_view_map=measure_to_view_map)

        tags = {'testtag1': 'testtag1val'}
        measurement_map.record(tag_map_tags=tags)
        self.assertTrue(measure_to_view_map.record.called)

    def test_record_against_implicit_tag_map(self):
        measure_to_view_map = mock.Mock()
        measurement_map = measurement_map_module.MeasurementMap(
            measure_to_view_map=measure_to_view_map)

        tags = {'testtag1': 'testtag1val'}
        execution_context.set_current_tag_map(tags)
        measurement_map.record()
        self.assertTrue(measure_to_view_map.record.called)
