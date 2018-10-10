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


class TimeSeries(object):
    """Time series data for a given metric and time interval.

    This class implements the spec for v1 TimeSeries structs as of
    opencensus-proto release v0.0.2. See opencensus-proto for details:

        https://github.com/census-instrumentation/opencensus-proto/blob/24333298e36590ea0716598caacc8959fc393c48/src/opencensus/proto/metrics/v1/metrics.proto#L112  # noqa

    A TimeSeries is a collection of data points that describes the time-varying
    values of a metric.

    :type start_timestamp: int
    :param start_timestamp: The time when the cumulative value was reset to
    zero.

    :type label_values: list(:class:
    '~opencensus.metrics.label_value.LabelValue')
    :param label_values: The set of label values that uniquely identify this
    timeseries.

    :type points: list(:class: '~opencensus.metrics.export.point.Point')
    :param points: The data points of this timeseries.
    """

    def __init__(self, start_timestamp, label_values, points):
        self._start_timestamp = start_timestamp
        self._label_values = label_values
        self._points = points

    @property
    def start_timestamp(self):
        return self._start_timestamp

    @property
    def label_values(self):
        return self._label_values

    @property
    def points(self):
        return self._points
