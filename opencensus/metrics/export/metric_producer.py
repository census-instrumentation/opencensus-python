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

import threading

from opencensus.metrics.export.meter import MetricType
from opencensus.metrics.export import metric_utils

class MetricProducer(object):
    """Produces a set of metrics for export."""

    def __init__(self, meter):
        self._meter = meter

    def get_metrics(self):
        """Get a set of metrics to be exported.

        :rtype: set(:class: `opencensus.metrics.export.metric.Metric`)
        :return: A set of metrics to be exported.
        """
        # Get raw measurements
        if MetricType.MEASURE in self._meter.builders and self._meter.builders[MetricType.MEASURE].has_measurement():
            return [metric_utils.measure_to_metric(self._meter.builders[MetricType.MEASURE])]
        else:
            return []

