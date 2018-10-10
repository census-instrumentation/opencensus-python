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

from opencensus.metrics.export.metric_descriptor import MetricDescriptorType

from opencensus.metrics.export.value import ValueLong
from opencensus.metrics.export.value import ValueDouble
from opencensus.metrics.export.value import ValueSummary
from opencensus.metrics.export.value import ValueDistribution


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

    def __init__(self, time_series, descriptor):
        if not time_series:
            raise ValueError
        if descriptor is None:
            raise ValueError
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
        check_type = None
        if self.descriptor.type in (MetricDescriptorType.GAUGE_INT64,
                                    MetricDescriptorType.CUMULATIVE_INT64):
            check_type = ValueLong
        elif self.descriptor.type in (MetricDescriptorType.GAUGE_DOUBLE,
                                      MetricDescriptorType.CUMULATIVE_DOUBLE):
            check_type = ValueDouble
        elif self.descriptor.type in (
                MetricDescriptorType.GAUGE_DISTRIBUTION,
                MetricDescriptorType.CUMULATIVE_DISTRIBUTION):
            check_type = ValueDistribution
        elif self.descriptor.type == MetricDescriptorType.SUMMARY:
            check_type = ValueSummary
        else:
            raise ValueError("Unknown metric descriptor type")
        for ts in self.time_series:
            if not ts.check_points_type(check_type):
                raise ValueError("Invalid point value type")
