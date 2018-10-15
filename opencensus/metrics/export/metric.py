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

from opencensus.metrics.export import metric_descriptor
from opencensus.metrics.export import value


class Metric(object):
    """A collection of time series data and label metadata.

    This class implements the spec for v1 Metrics as of opencensus-proto
    release v0.0.2. See opencensus-proto for details:

        https://github.com/census-instrumentation/opencensus-proto/blob/24333298e36590ea0716598caacc8959fc393c48/src/opencensus/proto/metrics/v1/metrics.proto#33  # noqa

    Defines a Metric which has one or more timeseries.

    :type descriptor: class: '~opencensus.metrics.export.metric_descriptor.MetricDescriptor'  # noqa
    :param descriptor: The metric's descriptor.

    :type timeseries: list(:class: '~opencensus.metrics.export.time_series.TimeSeries')
    :param timeseries: One or more timeseries for a single metric, where each
    timeseries has one or more points.
    """

    def __init__(self, descriptor, time_series):
        if not time_series:
            raise ValueError("time_series must not be empty or null")
        if descriptor is None:
            raise ValueError("descriptor must not be null")
        self._time_series = time_series
        self._descriptor = descriptor
        self._check_type()

    @property
    def time_series(self):
        return self._time_series

    @property
    def descriptor(self):
        return self._descriptor

    def _check_type(self):
        """Check that point value types match the descriptor type."""
        check_type = None
        if self.descriptor.type in (
                metric_descriptor.MetricDescriptorType.GAUGE_INT64,
                metric_descriptor.MetricDescriptorType.CUMULATIVE_INT64):
            check_type = value.ValueLong
        elif self.descriptor.type in (
                metric_descriptor.MetricDescriptorType.GAUGE_DOUBLE,
                metric_descriptor.MetricDescriptorType.CUMULATIVE_DOUBLE):
            check_type = value.ValueDouble
        elif self.descriptor.type in (
                metric_descriptor.MetricDescriptorType.GAUGE_DISTRIBUTION,
                metric_descriptor.MetricDescriptorType.CUMULATIVE_DISTRIBUTION
        ):
            check_type = value.ValueDistribution
        elif self.descriptor.type == (
                metric_descriptor.MetricDescriptorType.SUMMARY):
            check_type = value.ValueSummary
        else:
            raise ValueError("Unknown metric descriptor type")
        for ts in self.time_series:
            if not ts.check_points_type(check_type):
                raise ValueError("Invalid point value type")

    def _check_start_timestamp(self):
        """Check that starting timestamp exists for cumulative metrics."""
        if self.descriptor.type in (
                metric_descriptor.MetricDescriptorType.CUMULATIVE_INT64,
                metric_descriptor.MetricDescriptorType.CUMULATIVE_DOUBLE,
                metric_descriptor.MetricDescriptorType.CUMULATIVE_DISTRIBUTION,
        ):
            for ts in self.time_series:
                if ts.start_timestamp is None:
                    raise ValueError("time_series.start_timestamp must exist "
                                     "for cumulative metrics")
