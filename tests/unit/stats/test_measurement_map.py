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

import mock
import unittest

from opencensus.stats import measurement_map as measurement_map_module
from opencensus.tags import Tag
from opencensus.tags import TagContext
from opencensus.tags import TagMap

logger_patch = mock.patch('opencensus.stats.measurement_map.logger')


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
        with self.assertRaisesRegexp(
                TypeError,
                'attachment key should not be empty and should be a string'):
            measurement_map.measure_put_attachment(test_key, test_value)

    def test_put_attachment_none_value(self):
        measure_to_view_map = mock.Mock()
        test_key = 'testKey'
        test_value = None
        measurement_map = measurement_map_module.MeasurementMap(
            measure_to_view_map=measure_to_view_map, attachments={})
        with self.assertRaisesRegexp(
                TypeError,
                'attachment value should not be empty and should be a string'):
            measurement_map.measure_put_attachment(test_key, test_value)

    def test_put_attachment_int_key(self):
        measure_to_view_map = mock.Mock()
        test_key = 42
        test_value = 'testValue'
        measurement_map = measurement_map_module.MeasurementMap(
            measure_to_view_map=measure_to_view_map, attachments={})
        with self.assertRaisesRegexp(
                TypeError,
                'attachment key should not be empty and should be a string'):
            measurement_map.measure_put_attachment(test_key, test_value)

    def test_put_attachment_int_value(self):
        measure_to_view_map = mock.Mock()
        test_key = 'testKey'
        test_value = 42
        measurement_map = measurement_map_module.MeasurementMap(
            measure_to_view_map=measure_to_view_map, attachments={})
        with self.assertRaisesRegexp(
                TypeError,
                'attachment value should not be empty and should be a string'):
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
        test_value = 'testValue'
        measurement_map = measurement_map_module.MeasurementMap(
            measure_to_view_map=measure_to_view_map)
        measurement_map.measure_put_attachment(test_key, test_value)
        self.assertEqual({'testKey': 'testValue'}, measurement_map.attachments)

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
        measurement_map.record(tags=tags)
        self.assertTrue(measure_to_view_map.record.called)

    def test_record_against_implicit_tag_map(self):
        measure_to_view_map = mock.Mock()
        measurement_map = measurement_map_module.MeasurementMap(
            measure_to_view_map=measure_to_view_map)
        TagContext.set(TagMap(tags=[Tag('testtag1', 'testtag1val')]))
        measurement_map.record()
        self.assertTrue(measure_to_view_map.record.called)

    def test_record_negative_value(self):
        """Check that we refuse to record negative measurements."""
        measurement_map = measurement_map_module.MeasurementMap(mock.Mock())
        measurement_map.measure_int_put(mock.Mock(), 1)
        measurement_map.measure_int_put(mock.Mock(), -1)

        with logger_patch as mock_logger:
            measurement_map.record()

        self.assertTrue(measurement_map._invalid)
        measurement_map._measure_to_view_map.record.assert_not_called()
        mock_logger.warning.assert_called_once()

    def test_record_previous_negative_value(self):
        """Check that negative measurements poison the map."""
        measurement_map = measurement_map_module.MeasurementMap(mock.Mock())
        measure = mock.Mock()
        measurement_map.measure_int_put(measure, 1)

        measurement_map.record()
        self.assertFalse(measurement_map._invalid)
        measurement_map._measure_to_view_map.record.assert_called_once()

        measurement_map.measure_int_put(measure, -1)
        measurement_map._measure_to_view_map = mock.Mock()

        with logger_patch as mock_logger:
            measurement_map.record()

        self.assertTrue(measurement_map._invalid)
        measurement_map._measure_to_view_map.record.assert_not_called()
        mock_logger.warning.assert_called_once()

        measurement_map.measure_int_put(measure, 1)

        with logger_patch as another_mock_logger:
            measurement_map.record()

        self.assertTrue(measurement_map._invalid)
        measurement_map._measure_to_view_map.record.assert_not_called()
        another_mock_logger.warning.assert_called_once()

    def test_log_negative_puts(self):
        """Check that we warn against negative measurements on put."""
        measurement_map = measurement_map_module.MeasurementMap(mock.Mock())

        with logger_patch as mock_logger:
            measurement_map.measure_int_put(mock.Mock(), -1)
        mock_logger.warning.assert_called_once()

        with logger_patch as another_mock_logger:
            measurement_map.measure_float_put(mock.Mock(), -1.0)
        another_mock_logger.warning.assert_called_once()
