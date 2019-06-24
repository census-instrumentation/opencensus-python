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


from opencensus.ext.azure.common import Options
from opencensus.metrics.export.metric_descriptor import MetricDescriptorType
from opencensus.metrics import transport
from opencensus.stats import stats
from opencensus.ext.azure.common import utils
from opencensus.ext.azure.common.protocol import Data
from opencensus.ext.azure.common.protocol import DataPoint
from opencensus.ext.azure.common.protocol import Envelope
from opencensus.ext.azure.common.protocol import MetricData
from opencensus.ext.azure.common.transport import TransportMixin

__all__ = ['MetricsExporter', 'new_metrics_exporter']


class MetricsExporter(TransportMixin):
    """Metrics exporter for Microsoft Azure Monitor."""

    def __init__(self, options=None):
        if options is None:
            options = Options()
        self.options = options
        if not self.options.instrumentation_key:
            raise ValueError('The instrumentation_key is not provided.')

    def export_metrics(self, metrics):
        if not metrics:
            return
        envelopes = []
        for metric in metrics:
            # No support for histogram aggregations
            if metric.descriptor.type == MetricDescriptorType.CUMULATIVE_DISTRIBUTION:
                continue
            envelopes.append(self.metric_to_envelope(metric))
        if not envelopes:
            return
        self._transmit(envelopes)

    def metric_to_envelope(self, metric):
        # The timestamp is when the metric was recorded
        timestamp = metric.time_series[0].points[0].timestamp
        envelope = Envelope(
            iKey=self.options.instrumentation_key,
            tags=dict(utils.azure_monitor_context),
            time=timestamp.isoformat(),
        )
        envelope.name = 'Microsoft.ApplicationInsights.Metric'
        data = MetricData(
            metrics=self.metric_to_data_points(metric),
            properties=self.get_metric_properties(metric)
        )
        envelope.data = Data(baseData=data, baseType="MetricData")
        return envelope

    def metric_to_data_points(self, metric):
        """Convert an metric's OC time series to list of Azure data points."""
        data_points = []
        # Each time series will be uniquely identified by it's label values
        for time_series in metric.time_series:
            # Using stats, time_series should only have one point
            # which contains the aggregated value
            for point in time_series.points:
                data_point = DataPoint(ns=metric.descriptor.name,
                                       name=metric.descriptor.name,
                                       value=point.value.value)
                data_points.append(data_point)
        return data_points

    def get_metric_properties(self, metric):
        properties = {}
        # We will use only the first time series' label values for properties
        # Soon, only one time series will be present per metric
        for i in range(len(metric.descriptor.label_keys)):
            # We construct a properties map from the label keys and values
            # We assume the ordering is already correct
            if metric.time_series[0].label_values[i].value is None:
                value = "None"
            else:
                value = metric.time_series[0].label_values[i].value
            properties[metric.descriptor.label_keys[i].key] = value
        return properties


def new_metrics_exporter(**options):
    options = Options(**options)
    exporter = MetricsExporter(options=options)
    transport.get_exporter_thread(stats.stats,
                                  exporter,
                                  interval=options.export_interval)
    return exporter
