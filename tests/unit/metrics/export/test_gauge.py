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

import gc
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

    def test_get_value(self):
        point = gauge.GaugePointLong()
        point.set(10)
        self.assertEqual(point.value, 10)
        self.assertEqual(point.get_value(), point.value)


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

    def test_get_value(self):
        point = gauge.GaugePointDouble()
        point.set(10.1)
        self.assertEqual(point.value, 10.1)
        self.assertEqual(point.get_value(), point.value)


class TestDerivedGaugePoint(unittest.TestCase):
    def test_get_value(self):
        mock_fn = Mock()
        mock_value = Mock(spec=int)
        mock_fn.return_value = mock_value

        point = gauge.DerivedGaugePoint(mock_fn, gauge.GaugePointLong())
        mock_fn.assert_not_called()

        value = point.get_value()
        self.assertEqual(value, mock_value)
        self.assertEqual(point.gauge_point.value, mock_value)
        mock_fn.assert_called_once()

        value = point.get_value()
        self.assertEqual(value, mock_value)
        self.assertEqual(point.gauge_point.value, mock_value)
        self.assertEqual(mock_fn.call_count, 2)

    def test_get_value_gcd(self):
        """Check handling deletion of the underlying func."""
        get_10 = lambda: 10  # noqa
        point = gauge.DerivedGaugePoint(get_10, gauge.GaugePointLong())

        value = point.get_value()
        self.assertEqual(value, 10)
        self.assertEqual(point.gauge_point.value, 10)

        del get_10
        gc.collect()
        deleted_value = point.get_value()
        self.assertIsNone(deleted_value)
        # Check that we don't null out the underlying point value
        self.assertEqual(point.gauge_point.value, 10)

    def test_get_to_point_value(self):
        mock_fn = Mock()
        mock_value = Mock(spec=int)
        mock_fn.return_value = mock_value

        point = gauge.DerivedGaugePoint(mock_fn, gauge.GaugePointLong())
        mock_fn.assert_not_called()

        value_long = point.to_point_value()
        self.assertEqual(value_long.value, mock_value)
        self.assertEqual(point.gauge_point.value, mock_value)
        mock_fn.assert_called_once()

        value = point.get_value()
        self.assertEqual(value, mock_value)
        self.assertEqual(point.gauge_point.value, mock_value)
        self.assertEqual(mock_fn.call_count, 2)

    def test_get_to_point_value_gcd(self):
        get_10 = lambda: 10  # noqa
        point = gauge.DerivedGaugePoint(get_10, gauge.GaugePointLong())
        del get_10
        gc.collect()
        deleted_long_value = point.to_point_value()
        self.assertIsNone(deleted_long_value)


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
            long_gauge.get_or_create_time_series(None)
        with self.assertRaises(ValueError):
            long_gauge.get_or_create_time_series([Mock()])
        with self.assertRaises(ValueError):
            long_gauge.get_or_create_time_series([Mock(), Mock(), Mock()])
        with self.assertRaises(ValueError):
            long_gauge.get_or_create_time_series([Mock(), None])

        label_values = [Mock(), Mock()]
        point = long_gauge.get_or_create_time_series(label_values)
        self.assertIsInstance(point, gauge.GaugePointLong)
        self.assertEqual(point.value, 0)
        self.assertEqual(len(long_gauge.points.keys()), 1)
        [key] = long_gauge.points.keys()
        self.assertEqual(key, tuple(label_values))
        point2 = long_gauge.get_or_create_time_series(label_values)
        self.assertIs(point, point2)
        self.assertEqual(len(long_gauge.points.keys()), 1)

    def test_get_default_time_series(self):
        long_gauge = gauge.LongGauge(Mock(), Mock(), Mock(), [Mock(), Mock])
        default_point = long_gauge.get_or_create_default_time_series()
        self.assertIsInstance(default_point, gauge.GaugePointLong)
        self.assertEqual(default_point.value, 0)
        self.assertEqual(len(long_gauge.points.keys()), 1)

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
        long_gauge.get_or_create_time_series(lv1)
        lv2 = [Mock(), Mock()]
        long_gauge.get_or_create_time_series(lv2)
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

        long_gauge.get_or_create_default_time_series()
        self.assertEqual(len(long_gauge.points.keys()), 1)
        long_gauge.remove_default_time_series()
        self.assertEqual(len(long_gauge.points.keys()), 0)

    def test_clear(self):
        name = Mock()
        description = Mock()
        unit = Mock()
        label_keys = [Mock(), Mock]
        long_gauge = gauge.LongGauge(name, description, unit, label_keys)

        label_values = [Mock(), Mock()]
        point = long_gauge.get_or_create_time_series(label_values)
        self.assertEqual(len(long_gauge.points.keys()), 1)
        point.add(1)

        long_gauge.clear()
        self.assertDictEqual(long_gauge.points, {})

        label_values = [Mock(), Mock()]
        point2 = long_gauge.get_or_create_time_series(label_values)
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
        point1 = long_gauge.get_or_create_time_series(lv1)
        point2 = long_gauge.get_or_create_time_series(lv2)

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

        default_point = long_gauge.get_or_create_default_time_series()
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
        point = double_gauge.get_or_create_time_series([Mock(), Mock()])
        self.assertIsInstance(point, gauge.GaugePointDouble)

    def test_get_metric(self):
        double_gauge = gauge.DoubleGauge(Mock(), Mock(), Mock(),
                                         [Mock(), Mock])

        timestamp = Mock()

        lv1 = [Mock(), Mock()]
        lv2 = [Mock(), Mock()]
        point1 = double_gauge.get_or_create_time_series(lv1)
        point2 = double_gauge.get_or_create_time_series(lv2)

        point1.set(1.2)
        point2.set(2.2)
        metric = double_gauge.get_metric(timestamp)
        self.assertIsInstance(metric.time_series[0].points[0].value,
                              value_module.ValueDouble)
        self.assertIsInstance(metric.time_series[1].points[0].value,
                              value_module.ValueDouble)
        self.assertEqual(metric.time_series[0].points[0].value.value, 1.2)
        self.assertEqual(metric.time_series[1].points[0].value.value, 2.2)


class TestDerivedGauge(unittest.TestCase):

    def test_one(self):
        name = Mock()
        description = Mock()
        unit = Mock()
        label_keys = [Mock(), Mock]
        derived_gauge = gauge.DerivedLongGauge(
            name, description, unit, label_keys)
        self.assertEqual(derived_gauge.descriptor.name, name)
        self.assertEqual(derived_gauge.descriptor.description, description)
        self.assertEqual(derived_gauge.descriptor.unit, unit)
        self.assertEqual(derived_gauge.descriptor.label_keys, label_keys)
        self.assertEqual(derived_gauge.descriptor.type,
                         metric_descriptor.MetricDescriptorType.GAUGE_INT64)

    def test_create_time_series(self):
        name = Mock()
        description = Mock()
        unit = Mock()
        label_keys = [Mock(), Mock]
        derived_gauge = gauge.DerivedLongGauge(
            name, description, unit, label_keys)
        with self.assertRaises(ValueError):
            derived_gauge.create_time_series(None, Mock())
        with self.assertRaises(ValueError):
            derived_gauge.create_time_series([Mock()], Mock())
        with self.assertRaises(ValueError):
            derived_gauge.create_time_series([Mock(), None], Mock())
        with self.assertRaises(ValueError):
            derived_gauge.create_time_series([Mock(), Mock()], None)

        mock_fn = Mock()
        mock_fn.side_effect = range(10, 12)
        label_values = [Mock(), Mock()]
        point = derived_gauge.create_time_series(label_values, mock_fn)
        self.assertIsInstance(point, gauge.DerivedGaugePoint)
        self.assertIsInstance(point.gauge_point, gauge.GaugePointLong)
        mock_fn.assert_not_called()
        self.assertEqual(len(derived_gauge.points.keys()), 1)
        [key] = derived_gauge.points.keys()
        self.assertEqual(key, tuple(label_values))
        self.assertEqual(point.get_value(), 10)
        mock_fn.assert_called_once()
        self.assertEqual(point.get_value(), 11)
        self.assertEqual(mock_fn.call_count, 2)

        unused_mock_fn = Mock()
        point2 = derived_gauge.create_time_series(label_values, unused_mock_fn)
        self.assertIs(point, point2)
        unused_mock_fn.assert_not_called()
        self.assertEqual(len(derived_gauge.points.keys()), 1)

    def test_create_default_time_series(self):
        derived_gauge = gauge.DerivedLongGauge(
            Mock(), Mock(), Mock(), [Mock(), Mock])
        mock_fn = Mock()
        mock_fn.side_effect = range(10, 13)

        with self.assertRaises(ValueError):
            derived_gauge.create_default_time_series(None)

        default_point = derived_gauge.create_default_time_series(mock_fn)
        self.assertIsInstance(default_point, gauge.DerivedGaugePoint)
        self.assertIsInstance(default_point.gauge_point, gauge.GaugePointLong)
        self.assertEqual(default_point.get_value(), 10)
        self.assertEqual(len(derived_gauge.points.keys()), 1)

        unused_mock_fn = Mock()
        point2 = derived_gauge.create_default_time_series(unused_mock_fn)
        self.assertIs(default_point, point2)
        self.assertEqual(default_point.get_value(), 11)
        unused_mock_fn.assert_not_called()

        unused_mock_fn2 = Mock()
        point3 = derived_gauge._create_time_series(
            derived_gauge.default_label_values, unused_mock_fn)
        self.assertIs(default_point, point3)
        self.assertEqual(default_point.get_value(), 12)
        unused_mock_fn2.assert_not_called()


class TestRegistry(unittest.TestCase):
    def test_add_gauge(self):
        reg = gauge.Registry()

        with self.assertRaises(ValueError):
            reg.add_gauge(None)

        gauge1 = Mock()
        gauge1.descriptor.name = 'gauge1'
        gauge2 = Mock()
        gauge2.descriptor.name = 'gauge2'

        reg.add_gauge(gauge1)
        self.assertDictEqual(reg.gauges, {'gauge1': gauge1})
        reg.add_gauge(gauge2)
        self.assertDictEqual(reg.gauges, {'gauge1': gauge1, 'gauge2': gauge2})

        with self.assertRaises(ValueError):
            reg.add_gauge(gauge2)

    def test_get_metrics(self):
        reg = gauge.Registry()

        with self.assertRaises(ValueError):
            reg.add_gauge(None)

        gauge1 = Mock()
        gauge1.descriptor.name = 'gauge1'
        metric1 = Mock()
        gauge1.get_metric.return_value = metric1

        gauge2 = Mock()
        gauge2.descriptor.name = 'gauge2'
        metric2 = Mock()
        gauge2.get_metric.return_value = metric2

        self.assertSetEqual(reg.get_metrics(), set())
        reg.add_gauge(gauge1)
        self.assertSetEqual(reg.get_metrics(), {metric1})
        reg.add_gauge(gauge2)
        self.assertSetEqual(reg.get_metrics(), {metric1, metric2})
