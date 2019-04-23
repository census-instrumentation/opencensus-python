# Copyright 2019, OpenCensus Authors
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

from mock import Mock

from opencensus.metrics.export import cumulative
from opencensus.metrics.export import gauge
from opencensus.metrics.export import metric_descriptor
from opencensus.metrics.export import value as value_module


class TestCumulativePointLong(unittest.TestCase):
    def test_init(self):
        point = cumulative.CumulativePointLong()
        self.assertEqual(point.value, 0)
        self.assertIsInstance(point.value, int)

    def test_add(self):
        point = cumulative.CumulativePointLong()
        point.add(10)
        self.assertEqual(point.value, 10)
        point.add(-1)
        self.assertEqual(point.value, 10)
        # Check that we report type errors for args that we'd otherwise ignore
        with self.assertRaises(ValueError):
            point.add(-1.0)
        with self.assertRaises(ValueError):
            point.add(10.0)

    def test_get_value(self):
        point = cumulative.CumulativePointLong()
        point.add(10)
        self.assertEqual(point.value, 10)
        self.assertEqual(point.get_value(), point.value)


class TestCumulativePointDouble(unittest.TestCase):
    def test_init(self):
        point = cumulative.CumulativePointDouble()
        self.assertEqual(point.value, 0.0)
        self.assertIsInstance(point.value, float)

    def test_add(self):
        point = cumulative.CumulativePointDouble()
        point.add(10)
        self.assertEqual(point.value, 10.0)
        point.add(-1.0)
        self.assertEqual(point.value, 10.0)

    def test_get_value(self):
        point = cumulative.CumulativePointDouble()
        point.add(10.1)
        self.assertEqual(point.value, 10.1)
        self.assertEqual(point.get_value(), point.value)


# TestLongCumulative and TestDoubleCumulative check that the reported value of
# a cumulative never decreases. We rely on the other tests to check the
# behavior these classes have in common with gauges.
class TestLongCumulative(unittest.TestCase):

    def test_get_metric(self):
        name = Mock()
        description = Mock()
        unit = Mock()
        label_keys = [Mock(), Mock]
        long_cumulative = cumulative.LongCumulative(
            name, description, unit, label_keys)

        self.assertEqual(
            long_cumulative.descriptor.type,
            metric_descriptor.MetricDescriptorType.CUMULATIVE_INT64)

        timestamp = Mock()
        null_metric = long_cumulative.get_metric(timestamp)
        self.assertIsNone(null_metric)

        lv1 = [Mock(), Mock()]
        lv2 = [Mock(), Mock()]
        point1 = long_cumulative.get_or_create_time_series(lv1)
        point2 = long_cumulative.get_or_create_time_series(lv2)

        metric = long_cumulative.get_metric(timestamp)
        self.assertEqual(metric.descriptor, long_cumulative.descriptor)
        self.assertEqual(len(metric.time_series), 2)
        self.assertEqual(len(metric.time_series[0].points), 1)
        self.assertEqual(len(metric.time_series[1].points), 1)
        self.assertIsInstance(metric.time_series[0].points[0].value,
                              value_module.ValueLong)
        self.assertIsInstance(metric.time_series[1].points[0].value,
                              value_module.ValueLong)
        self.assertEqual(metric.time_series[0].points[0].value.value, 0)
        self.assertEqual(metric.time_series[1].points[0].value.value, 0)

        timestamp2 = Mock()
        point1.add(2)
        point2.add(4)
        metric = long_cumulative.get_metric(timestamp2)
        self.assertEqual(metric.descriptor, long_cumulative.descriptor)
        self.assertEqual(len(metric.time_series), 2)
        self.assertEqual(len(metric.time_series[0].points), 1)
        self.assertEqual(len(metric.time_series[1].points), 1)
        self.assertIsInstance(metric.time_series[0].points[0].value,
                              value_module.ValueLong)
        self.assertIsInstance(metric.time_series[1].points[0].value,
                              value_module.ValueLong)
        self.assertEqual(metric.time_series[0].points[0].value.value, 2)
        self.assertEqual(metric.time_series[1].points[0].value.value, 4)

        timestamp3 = Mock()
        point1.add(1)
        point2.add(-1)
        metric = long_cumulative.get_metric(timestamp3)
        self.assertEqual(metric.descriptor, long_cumulative.descriptor)
        self.assertEqual(len(metric.time_series), 2)
        self.assertEqual(len(metric.time_series[0].points), 1)
        self.assertEqual(len(metric.time_series[1].points), 1)
        self.assertIsInstance(metric.time_series[0].points[0].value,
                              value_module.ValueLong)
        self.assertIsInstance(metric.time_series[1].points[0].value,
                              value_module.ValueLong)
        self.assertEqual(metric.time_series[0].points[0].value.value, 3)
        self.assertEqual(metric.time_series[1].points[0].value.value, 4)


class TestDoubleCumulative(unittest.TestCase):

    def test_get_metric(self):
        name = Mock()
        description = Mock()
        unit = Mock()
        label_keys = [Mock(), Mock]
        double_cumulative = cumulative.DoubleCumulative(
            name, description, unit, label_keys)

        self.assertEqual(
            double_cumulative.descriptor.type,
            metric_descriptor.MetricDescriptorType.CUMULATIVE_DOUBLE)

        timestamp = Mock()
        null_metric = double_cumulative.get_metric(timestamp)
        self.assertIsNone(null_metric)

        lv1 = [Mock(), Mock()]
        lv2 = [Mock(), Mock()]
        point1 = double_cumulative.get_or_create_time_series(lv1)
        point2 = double_cumulative.get_or_create_time_series(lv2)

        metric = double_cumulative.get_metric(timestamp)
        self.assertEqual(metric.descriptor, double_cumulative.descriptor)
        self.assertEqual(len(metric.time_series), 2)
        self.assertEqual(len(metric.time_series[0].points), 1)
        self.assertEqual(len(metric.time_series[1].points), 1)
        self.assertIsInstance(metric.time_series[0].points[0].value,
                              value_module.ValueDouble)
        self.assertIsInstance(metric.time_series[1].points[0].value,
                              value_module.ValueDouble)
        self.assertEqual(metric.time_series[0].points[0].value.value, 0)
        self.assertEqual(metric.time_series[1].points[0].value.value, 0)

        timestamp2 = Mock()
        point1.add(2.125)
        point2.add(1.125)
        metric = double_cumulative.get_metric(timestamp2)
        self.assertEqual(metric.descriptor, double_cumulative.descriptor)
        self.assertEqual(len(metric.time_series), 2)
        self.assertEqual(len(metric.time_series[0].points), 1)
        self.assertEqual(len(metric.time_series[1].points), 1)
        self.assertIsInstance(metric.time_series[0].points[0].value,
                              value_module.ValueDouble)
        self.assertIsInstance(metric.time_series[1].points[0].value,
                              value_module.ValueDouble)
        self.assertEqual(metric.time_series[0].points[0].value.value, 2.125)
        self.assertEqual(metric.time_series[1].points[0].value.value, 1.125)

        timestamp3 = Mock()
        point1.add(-1.125)
        point2.add(1.125)
        metric = double_cumulative.get_metric(timestamp3)
        self.assertEqual(metric.descriptor, double_cumulative.descriptor)
        self.assertEqual(len(metric.time_series), 2)
        self.assertEqual(len(metric.time_series[0].points), 1)
        self.assertEqual(len(metric.time_series[1].points), 1)
        self.assertIsInstance(metric.time_series[0].points[0].value,
                              value_module.ValueDouble)
        self.assertIsInstance(metric.time_series[1].points[0].value,
                              value_module.ValueDouble)
        self.assertEqual(metric.time_series[0].points[0].value.value, 2.125)
        self.assertEqual(metric.time_series[1].points[0].value.value, 2.25)


class TestDerivedLongCumulative(unittest.TestCase):

    def test_ts_point_type(self):
        derived_cumulative = cumulative.DerivedLongCumulative(
            Mock(), Mock(), Mock(), [Mock(), Mock])

        mock_fn = Mock()
        default_point = derived_cumulative.create_default_time_series(mock_fn)
        self.assertIsInstance(default_point, gauge.DerivedGaugePoint)
        self.assertIsInstance(default_point.gauge_point,
                              cumulative.CumulativePointLong)
        mock_fn.assert_not_called()

        point = derived_cumulative.create_time_series(
            [Mock(), Mock()], mock_fn)
        self.assertIsInstance(point, gauge.DerivedGaugePoint)
        self.assertIsInstance(point.gauge_point,
                              cumulative.CumulativePointLong)
        mock_fn.assert_not_called()

    def test_get_metric(self):
        derived_cumulative = cumulative.DerivedLongCumulative(
            Mock(), Mock(), Mock(), [])
        mock_fn = Mock()
        mock_fn.return_value = 123
        derived_cumulative.create_default_time_series(mock_fn)

        now1 = Mock()
        [ts] = derived_cumulative.get_metric(now1).time_series
        [ts_point] = ts.points
        self.assertEqual(ts_point.timestamp, now1)
        self.assertEqual(ts_point.value.value, 123)
        self.assertIsInstance(ts_point.value, value_module.ValueLong)

    def test_point_value_increases(self):
        derived_cumulative = cumulative.DerivedLongCumulative(
            Mock(), Mock(), Mock(), [])
        mock_fn = Mock()
        point = derived_cumulative.create_default_time_series(mock_fn)

        mock_fn.return_value = -10
        self.assertEqual(point.get_value(), 0)
        mock_fn.return_value = 10
        self.assertEqual(point.get_value(), 10)
        mock_fn.return_value = 9
        self.assertEqual(point.get_value(), 10)

    def test_raise_on_float(self):
        derived_cumulative = cumulative.DerivedLongCumulative(
            Mock(), Mock(), Mock(), [])
        mock_fn = Mock()
        mock_fn.return_value = 1.125
        point = derived_cumulative.create_default_time_series(mock_fn)

        with self.assertRaises(ValueError):
            point.get_value()


class TestDerivedDoubleCumulative(unittest.TestCase):

    def test_ts_point_type(self):
        derived_cumulative = cumulative.DerivedDoubleCumulative(
            Mock(), Mock(), Mock(), [Mock(), Mock])

        mock_fn = Mock()
        default_point = derived_cumulative.create_default_time_series(mock_fn)
        self.assertIsInstance(default_point, gauge.DerivedGaugePoint)
        self.assertIsInstance(default_point.gauge_point,
                              cumulative.CumulativePointDouble)
        mock_fn.assert_not_called()

        point = derived_cumulative.create_time_series(
            [Mock(), Mock()], mock_fn)
        self.assertIsInstance(point, gauge.DerivedGaugePoint)
        self.assertIsInstance(point.gauge_point,
                              cumulative.CumulativePointDouble)
        mock_fn.assert_not_called()

    def test_get_metric(self):
        derived_cumulative = cumulative.DerivedDoubleCumulative(
            Mock(), Mock(), Mock(), [])
        mock_fn = Mock()
        mock_fn.return_value = 1.23
        derived_cumulative.create_default_time_series(mock_fn)

        now1 = Mock()
        [ts] = derived_cumulative.get_metric(now1).time_series
        [ts_point] = ts.points
        self.assertEqual(ts_point.timestamp, now1)
        self.assertEqual(ts_point.value.value, 1.23)
        self.assertIsInstance(ts_point.value, value_module.ValueDouble)

    def test_point_value_increases(self):
        derived_cumulative = cumulative.DerivedDoubleCumulative(
            Mock(), Mock(), Mock(), [])
        mock_fn = Mock()
        point = derived_cumulative.create_default_time_series(mock_fn)

        mock_fn.return_value = -1.1
        self.assertEqual(point.get_value(), 0)
        mock_fn.return_value = 2.3
        self.assertEqual(point.get_value(), 2.3)
        mock_fn.return_value = 1.2
        self.assertEqual(point.get_value(), 2.3)
