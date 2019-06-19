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

from opencensus.metrics.export import metric_utils
from opencensus.metrics.export import execution_context
from opencensus.metrics.export import meter
from opencensus.metrics.export import measure


class MetricsProducer(object):
    """Produces a set of metrics for export."""

    def __init__(self):
        self.meter = meter.Meter()

    def get_metrics(self):
        """Get a set of metrics to be exported.

    :rtype: set(:class: `opencensus.metrics.export.metric.Metric`)
        :return: A set of metrics to be exported.
        """
        metrics = []
        # Get raw measurements to aggregated data
        for measure_, measurements in self.meter.measurements_map.items():
            if not measurements:
                continue
            aggregation_function = None
            if measure_.aggregation_type == measure.AggregationType.COUNT:
                aggregation_function = metric_utils.count_aggregation
            elif measure_.aggregation_type == measure.AggregationType.SUM:
                aggregation_function = metric_utils.sum_aggregation
            metrics.append(metric_utils.measurements_to_metric(measure_, aggregation_function, measurements))
        return metrics

metrics_producer = MetricsProducer()
