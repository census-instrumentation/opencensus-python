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

import time

from opencensus.ext.azure.common import Options
from opencensus.metrics import transport
from opencensus.metrics.export import metric_producer
from opencensus.metrics.export.metric_descriptor import MetricDescriptorType
from opencensus.metrics.export.value import ValueDistribution
from opencensus.ext.azure.common.protocol import Data
from opencensus.ext.azure.common.protocol import DataPoint
from opencensus.ext.azure.common.protocol import DataPointType
from opencensus.ext.azure.common.protocol import Envelope
from opencensus.ext.azure.common.protocol import MetricData
from opencensus.ext.azure.common import utils
from opencensus.ext.azure.common.transport import TransportMixin
from opencensus.stats import stats
from opencensus.stats import metric_utils


__all__ = ['MetricsExporter', 'new_metrics_exporter']


class MetricsExporter(TransportMixin):
    """Metrics exporter for Microsoft Azure Monitor."""

    def __init__(self, options):
        self.options = options
        if not self.options.instrumentation_key:
            raise ValueError('The instrumentation_key is not provided.')
        self._md_cache = {}
        self._md_lock = threading.Lock()

    def export_metrics(self, metrics):
        if metrics:
            metrics = list(metrics)
        envelopes = []
        for metric in metrics:
            # Does not support Histograms
            if metric.descriptor.type != MetricDescriptorType.SUMMARY:
                envelopes.append(self.metric_to_envelope(metric))
        self._transmit(envelopes)

    def metric_to_envelope(self, metric):
        envelope = Envelope(
            iKey=self.options.instrumentation_key,
            tags=dict(utils.azure_monitor_context),
            time=utils.timestamp_to_iso_str(time.time()),
        )
        envelope.name = 'Microsoft.ApplicationInsights.Metric'
        data = MetricData(
            namespace=metric.descriptor.name,
            metrics=self.metric_to_data_points(metric),
        )
        envelope.data = Data(baseData=data, baseType="MetricData")
        return envelope

    def metric_to_data_points(self, metric):
        """Convert an metric's OC time series to a list of Azure data points."""
        data_points = []
        data_point_type = DataPointType.AGGREGATION
        is_distribution_type = False
        if metric_utils.is_gauge(metric.descriptor.type):
            data_point_type = DataPointType.MEASUREMENT
        if MetricDescriptorType.to_type_class(metric.descriptor.type) == ValueDistribution:
            is_distribution_type = True
        
        for point in metric.time_series[0].points:
            if point.value is not None:
                value = None
                if is_distribution_type:
                    continue
                else:
                    value = point.value.value

                data_point = DataPoint(ns=metric.descriptor.name,
                                    name=metric.descriptor.name,
                                    value=value,
                                    count=None,
                                    min=None,
                                    max=None)
                data_points.append(data_point)
            return data_points


def new_metrics_exporter(**options):
    options = Options(**options)
    exporter = MetricsExporter(options=options)
    transport.get_exporter_thread(stats.stats,
                                  exporter,
                                  interval=options.export_interval)
    return exporter
