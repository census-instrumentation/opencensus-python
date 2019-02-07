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

from collections import OrderedDict
import six
import threading

from opencensus.metrics.export import metric
from opencensus.metrics.export import metric_descriptor
from opencensus.metrics.export import point as point_module
from opencensus.metrics.export import time_series
from opencensus.metrics.export import value as value_module


class GaugePointLong(object):
    """An instantaneous measurement from a LongGauge.

    A GaugePointLong represents the most recent measurement from a
    :class:`LongGauge` for a given set of label values.
    """

    def __init__(self):
        self.value = 0
        self._value_lock = threading.Lock()

    def __repr__(self):
        return ("{}({})"
                .format(
                    type(self).__name__,
                    self.value
                ))

    def add(self, val):
        """Add `val` to the current value.

        :type val: int
        :param val: Value to add.
        """
        if not isinstance(val, six.integer_types):
            raise ValueError("GaugePointLong only supports integer types")
        with self._value_lock:
            self.value += val

    def set(self, val):
        """Set the current value to `val`.

        :type val: int
        :param val: Value to set.
        """
        if not isinstance(val, six.integer_types):
            raise ValueError("GaugePointLong only supports integer types")
        with self._value_lock:
            self.value = val


class GaugePointDouble(object):
    """An instantaneous measurement from a DoubleGauge.

    A GaugePointDouble represents the most recent measurement from a
    :class:`DoubleGauge` for a given set of label values.
    """

    def __init__(self):
        self.value = 0.0
        self._value_lock = threading.Lock()

    def __repr__(self):
        return ("{}({})"
                .format(
                    type(self).__name__,
                    self.value
                ))

    def add(self, val):
        """Add `val` to the current value.

        :type val: float
        :param val: Value to add.
        """
        with self._value_lock:
            self.value += val

    def set(self, val):
        """Set the current value to `val`.

        :type val: float
        :param val: Value to set.
        """
        with self._value_lock:
            self.value = float(val)


class Gauge(object):
    """A set of instantaneous measurements of the same type.

    End users should use :class:`LongGauge` or :class:`DoubleGauge` instead of
    using this class directly.

    The constructor arguments are used to create a
    :class:`opencensus.metrics.export.metric_descriptor.MetricDescriptor` for
    converted metrics. See that class for details.
    """

    def __init__(self, name, description, unit, label_keys):
        self._len_label_keys = len(label_keys)
        self.descriptor = metric_descriptor.MetricDescriptor(
            name, description, unit, self.descriptor_type, label_keys)
        self.points = OrderedDict()
        self._points_lock = threading.Lock()

    def __repr__(self):
        return ('{}(descriptor.name="{}", points={})'
                .format(
                    type(self).__name__,
                    self.descriptor.name,
                    self.points
                ))

    def get_time_series(self, label_values):
        """Get a mutable measurement for the given set of label values.

        :type label_values: list(:class:`LabelValue`)
        :param label_values: The measurement's label values.

        :rtype: :class:`GaugePointLong` or :class:`GaugePointDouble`
        :return: A mutable point that represents the last value of the
        measurement.
        """
        if label_values is None:
            raise ValueError
        if any(lv is None for lv in label_values):
            raise ValueError
        if len(label_values) != self._len_label_keys:
            raise ValueError
        with self._points_lock:
            return self.points.setdefault(
                tuple(label_values), self.point_type())

    def remove_time_series(self, label_values):
        """Remove the time series for specific label values.

        :type label_values: list(:class:`LabelValue`)
        :param label_values: Label values of the time series to remove.
        """
        if label_values is None:
            raise ValueError
        if any(lv is None for lv in label_values):
            raise ValueError
        if len(label_values) != self._len_label_keys:
            raise ValueError
        with self._points_lock:
            try:
                del self.points[tuple(label_values)]
            except KeyError:
                pass

    def clear(self):
        """Remove all points from this gauge."""
        with self._points_lock:
            self.points = OrderedDict()

    def get_metric(self, timestamp):
        """Get a metric including all current time series.

        Get a :class:`opencensus.metrics.export.metric.Metric` with one
        :class:`opencensus.metrics.export.time_series.TimeSeries` for each
        set of label values with a recorded measurement. Each `TimeSeries`
        has a single point that represents the last recorded value.

        :type timestamp: :class:`datetime.datetime`
        :param timestamp: Recording time to report, usually the current time.

        :rtype: :class:`opencensus.metrics.export.metric.Metric` or None
        :return: A converted metric for all current measurements.
        """
        if not self.points:
            return None

        ts_list = []
        for lv, gp in self.points.items():
            point = point_module.Point(self.value_type(gp.value), timestamp)
            ts_list.append(time_series.TimeSeries(lv, [point], timestamp))
        return metric.Metric(self.descriptor, ts_list)

    @property
    def descriptor_type(self):  # pragma: NO COVER
        raise NotImplementedError

    @property
    def point_type(self):  # pragma: NO COVER
        raise NotImplementedError

    @property
    def value_type(self):  # pragma: NO COVER
        raise NotImplementedError


class LongGauge(Gauge):
    """Gauge for recording int-valued measurements."""
    descriptor_type = metric_descriptor.MetricDescriptorType.GAUGE_INT64
    point_type = GaugePointLong
    value_type = value_module.ValueLong


class DoubleGauge(Gauge):
    """Gauge for recording float-valued measurements."""
    descriptor_type = metric_descriptor.MetricDescriptorType.GAUGE_DOUBLE
    point_type = GaugePointDouble
    value_type = value_module.ValueDouble
