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

try:
    from mock import Mock
except ImportError:
    from unittest.mock import Mock

import unittest

from opencensus.metrics.export import gauge
from opencensus.metrics.export import metric_descriptor
from opencensus.metrics.export import value as value_module


class TestGaugePointLong(unittest.TestCase):
    def test_init(self):
        point = gauge.GaugePointLong()
        self.assertEqual(point.value, 0)
        self.assertIsInstance(point.value, int)

    def test_add(self):
        point = gauge.GaugePointLong()
        point.add(10)
        self.assertEqual(point.value, 10)
        point.add(-20)
        self.assertEqual(point.value, -10)
        with self.assertRaises(ValueError):
            point.add(10.0)

    def test_set(self):
        point = gauge.GaugePointLong()
        point.set(10)
        self.assertEqual(point.value, 10)
        point.set(-20)
        self.assertEqual(point.value, -20)
        with self.assertRaises(ValueError):
            point.set(10.0)


class TestGaugePointDouble(unittest.TestCase):
    def test_init(self):
        point = gauge.GaugePointDouble()
        self.assertEqual(point.value, 0.0)
        self.assertIsInstance(point.value, float)

    def test_add(self):
        point = gauge.GaugePointDouble()
        point.add(10)
        self.assertEqual(point.value, 10.0)
        point.add(-20.2)
        self.assertEqual(point.value, -10.2)

    def test_set(self):
        point = gauge.GaugePointDouble()
        point.set(10)
        self.assertEqual(point.value, 10.0)
        point.set(-20.2)
        self.assertEqual(point.value, -20.2)


class TestLongGauge(unittest.TestCase):
    def test_init(self):
        name = Mock()
        description = Mock()
        unit = Mock()
        label_keys = [Mock(), Mock]
        long_gauge = gauge.LongGauge(name, description, unit, label_keys)
        self.assertEqual(long_gauge.descriptor.name, name)
        self.assertEqual(long_gauge.descriptor.description, description)
        self.assertEqual(long_gauge.descriptor.unit, unit)
        self.assertEqual(long_gauge.descriptor.label_keys, label_keys)
        self.assertEqual(long_gauge.descriptor.type,
                         metric_descriptor.MetricDescriptorType.GAUGE_INT64)

    def test_get_time_series(self):
        name = Mock()
        description = Mock()
        unit = Mock()
        label_keys = [Mock(), Mock]
        long_gauge = gauge.LongGauge(name, description, unit, label_keys)
        with self.assertRaises(ValueError):
            long_gauge.get_time_series(None)
        with self.assertRaises(ValueError):
            long_gauge.get_time_series([Mock()])
        with self.assertRaises(ValueError):
            long_gauge.get_time_series([Mock(), Mock(), Mock()])
        with self.assertRaises(ValueError):
            long_gauge.get_time_series([Mock(), None])

        label_values = [Mock(), Mock()]
        point = long_gauge.get_time_series(label_values)
        self.assertIsInstance(point, gauge.GaugePointLong)
        self.assertEqual(point.value, 0)
        self.assertEqual(len(long_gauge.points.keys()), 1)
        [key] = long_gauge.points.keys()
        self.assertEqual(key, tuple(label_values))
        point2 = long_gauge.get_time_series(label_values)
        self.assertIs(point, point2)
        self.assertEqual(len(long_gauge.points.keys()), 1)

    def test_get_default_time_series(self):
        long_gauge = gauge.LongGauge(Mock(), Mock(), Mock(), [Mock(), Mock])
        default_point = long_gauge.get_default_time_series()
        self.assertIsInstance(default_point, gauge.GaugePointLong)
        self.assertEqual(long_gauge.default_point, default_point)
        self.assertEqual(default_point.value, 0)

    def test_remove_time_series(self):
        long_gauge = gauge.LongGauge(Mock(), Mock(), Mock(), [Mock(), Mock()])

        with self.assertRaises(ValueError):
            long_gauge.remove_time_series(None)
        with self.assertRaises(ValueError):
            long_gauge.remove_time_series([Mock()])
        with self.assertRaises(ValueError):
            long_gauge.remove_time_series([Mock(), Mock(), Mock()])
        with self.assertRaises(ValueError):
            long_gauge.remove_time_series([Mock(), None])

        lv1 = [Mock(), Mock()]
        long_gauge.get_time_series(lv1)
        lv2 = [Mock(), Mock()]
        long_gauge.get_time_series(lv2)
        self.assertEqual(len(long_gauge.points.keys()), 2)

        # Removing a non-existent point shouldn't fail, or remove anything
        long_gauge.remove_time_series([Mock(), Mock()])
        self.assertEqual(len(long_gauge.points.keys()), 2)

        long_gauge.remove_time_series(lv1)
        self.assertEqual(len(long_gauge.points.keys()), 1)
        [key] = long_gauge.points.keys()
        self.assertEqual(key, tuple(lv2))

        long_gauge.remove_time_series(lv2)
        self.assertEqual(len(long_gauge.points.keys()), 0)

    def test_remove_default_time_series(self):
        long_gauge = gauge.LongGauge(Mock(), Mock(), Mock(), [Mock(), Mock()])

        # Removing the default point before it exists shouldn't fail
        long_gauge.remove_default_time_series()

        long_gauge.get_default_time_series()
        self.assertIsNotNone(long_gauge.default_point)
        long_gauge.remove_default_time_series()
        self.assertIsNone(long_gauge.default_point)

    def test_clear(self):
        name = Mock()
        description = Mock()
        unit = Mock()
        label_keys = [Mock(), Mock]
        long_gauge = gauge.LongGauge(name, description, unit, label_keys)

        label_values = [Mock(), Mock()]
        point = long_gauge.get_time_series(label_values)
        self.assertEqual(len(long_gauge.points.keys()), 1)
        point.add(1)

        long_gauge.clear()
        self.assertDictEqual(long_gauge.points, {})

        label_values = [Mock(), Mock()]
        point2 = long_gauge.get_time_series(label_values)
        self.assertEqual(point2.value, 0)
        self.assertIsNot(point, point2)

    def test_get_metric(self):
        name = Mock()
        description = Mock()
        unit = Mock()
        label_keys = [Mock(), Mock]
        long_gauge = gauge.LongGauge(name, description, unit, label_keys)

        timestamp = Mock()
        null_metric = long_gauge.get_metric(timestamp)
        self.assertIsNone(null_metric)

        lv1 = [Mock(), Mock()]
        lv2 = [Mock(), Mock()]
        point1 = long_gauge.get_time_series(lv1)
        point2 = long_gauge.get_time_series(lv2)

        point1.set(1)
        point2.set(2)
        metric = long_gauge.get_metric(timestamp)
        self.assertEqual(metric.descriptor, long_gauge.descriptor)
        self.assertEqual(len(metric.time_series), 2)
        self.assertEqual(len(metric.time_series[0].points), 1)
        self.assertEqual(len(metric.time_series[1].points), 1)
        self.assertIsInstance(metric.time_series[0].points[0].value,
                              value_module.ValueLong)
        self.assertIsInstance(metric.time_series[1].points[0].value,
                              value_module.ValueLong)
        self.assertEqual(metric.time_series[0].points[0].value.value, 1)
        self.assertEqual(metric.time_series[1].points[0].value.value, 2)

    def test_get_metric_default(self):
        name = Mock()
        description = Mock()
        unit = Mock()
        label_keys = [Mock(), Mock]
        long_gauge = gauge.LongGauge(name, description, unit, label_keys)

        default_point = long_gauge.get_default_time_series()
        default_point.set(3)

        timestamp = Mock()
        metric = long_gauge.get_metric(timestamp)
        self.assertEqual(metric.descriptor, long_gauge.descriptor)
        self.assertEqual(len(metric.time_series), 1)
        self.assertEqual(len(metric.time_series[0].points), 1)
        self.assertIsInstance(metric.time_series[0].points[0].value,
                              value_module.ValueLong)
        self.assertEqual(metric.time_series[0].points[0].value.value, 3)


class TestDoubleGauge(unittest.TestCase):

    # TestLongGauge does the heavy lifting, this test just checks that
    # DoubleGauge creates points and metrics of the right type
    def test_init(self):
        name = Mock()
        description = Mock()
        unit = Mock()
        label_keys = [Mock(), Mock]
        double_gauge = gauge.DoubleGauge(name, description, unit, label_keys)
        self.assertEqual(double_gauge.descriptor.type,
                         metric_descriptor.MetricDescriptorType.GAUGE_DOUBLE)

    def test_get_time_series(self):
        double_gauge = gauge.DoubleGauge(Mock(), Mock(), Mock(),
                                         [Mock(), Mock])
        point = double_gauge.get_time_series([Mock(), Mock()])
        self.assertIsInstance(point, gauge.GaugePointDouble)

    def test_get_metric(self):
        double_gauge = gauge.DoubleGauge(Mock(), Mock(), Mock(),
                                         [Mock(), Mock])

        timestamp = Mock()

        lv1 = [Mock(), Mock()]
        lv2 = [Mock(), Mock()]
        point1 = double_gauge.get_time_series(lv1)
        point2 = double_gauge.get_time_series(lv2)

        point1.set(1.2)
        point2.set(2.2)
        metric = double_gauge.get_metric(timestamp)
        self.assertIsInstance(metric.time_series[0].points[0].value,
                              value_module.ValueDouble)
        self.assertIsInstance(metric.time_series[1].points[0].value,
                              value_module.ValueDouble)
        self.assertEqual(metric.time_series[0].points[0].value.value, 1.2)
        self.assertEqual(metric.time_series[1].points[0].value.value, 2.2)
