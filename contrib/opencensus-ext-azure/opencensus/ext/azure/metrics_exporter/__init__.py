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
from opencensus.ext.azure.common import utils
from opencensus.ext.azure.common.protocol import Data
from opencensus.ext.azure.common.protocol import DataPoint
from opencensus.ext.azure.common.protocol import Envelope
from opencensus.ext.azure.common.protocol import MetricData
from opencensus.ext.azure.common.storage import LocalNoopStorage
from opencensus.ext.azure.common.transport import TransportMixin
from opencensus.metrics import transport
from opencensus.metrics.export.metric_descriptor import MetricDescriptorType
from opencensus.stats import stats

__all__ = ['MetricsExporter', 'new_metrics_exporter']


class MetricsExporter(TransportMixin):
    """Metrics exporter for Microsoft Azure Monitor."""

    def __init__(self, options=None):
        if options is None:
            options = Options()
        self.options = options
        if not self.options.instrumentation_key:
            raise ValueError('The instrumentation_key is not provided.')
        self.max_batch_size = self.options.max_batch_size
        self.storage = LocalNoopStorage(
            path=self.options.storage_path,
            max_size=self.options.storage_max_size,
            maintenance_period=self.options.storage_maintenance_period,
            retention_period=self.options.storage_retention_period,
        )

    def export_metrics(self, metrics):
        if metrics:
            envelopes = []
            for metric in metrics:
                # No support for histogram aggregations
                type_ = metric.descriptor.type
                if type_ != MetricDescriptorType.CUMULATIVE_DISTRIBUTION:
                    md = metric.descriptor
                    # Each time series will be uniquely
                    # identified by it's label values
                    for time_series in metric.time_series:
                        # Using stats, time_series should
                        # only have one point which contains
                        # the aggregated value
                        data_point = self.create_data_points(
                                     time_series, md)[0]
                        # The timestamp is when the metric was recorded
                        time_stamp = time_series.points[0].timestamp
                        # Get the properties using label keys from metric
                        # and label values of the time series
                        properties = self.create_properties(time_series, md)
                        envelopes.append(self.create_envelope(data_point,
                                                              time_stamp,
                                                              properties))
                        # Send data in batches of max_batch_size
                        if len(envelopes) == self.max_batch_size:
                            self._transmit(envelopes)
                            del envelopes[:]
            # if leftover data points in envelopes, send them all
            if envelopes:
                self._transmit(envelopes)

    def create_data_points(self, time_series, metric_descriptor):
        """Convert an metric's OC time series to list of Azure data points."""
        data_points = []
        for point in time_series.points:
            data_point = DataPoint(ns=metric_descriptor.name,
                                   name=metric_descriptor.name,
                                   value=point.value.value)
            data_points.append(data_point)
        return data_points

    def create_properties(self, time_series, metric_descriptor):
        properties = {}
        # We construct a properties map from the
        # label keys and values
        # We assume the ordering is already correct
        for i in range(len(metric_descriptor.label_keys)):
            if time_series.label_values[i].value is None:
                value = "None"
            else:
                value = time_series.label_values[i].value
            properties[metric_descriptor.label_keys[i].key] = value
        return properties

    def create_envelope(self, data_point, time_stamp, properties):
        envelope = Envelope(
            iKey=self.options.instrumentation_key,
            tags=dict(utils.azure_monitor_context),
            time=time_stamp.isoformat(),
        )
        envelope.name = "Microsoft.ApplicationInsights.Metric"
        data = MetricData(
            metrics=[data_point],
            properties=properties
        )
        envelope.data = Data(baseData=data, baseType="MetricData")
        return envelope


def new_metrics_exporter(**options):
    options = Options(**options)
    exporter = MetricsExporter(options=options)
    transport.get_exporter_thread(stats.stats,
                                  exporter,
                                  interval=options.export_interval)
    return exporter
