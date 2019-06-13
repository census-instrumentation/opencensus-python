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
from opencensus.ext.azure.common.protocol import Data
from opencensus.ext.azure.common.protocol import Envelope
from opencensus.ext.azure.common.protocol import MetricData
from opencensus.ext.azure.common import utils
from opencensus.ext.azure.common.transport import TransportMixin
from opencensus.stats import stats

__all__ = ['MetricsExporter', 'new_metrics_exporter']


class MetricsExporter(TransportMixin):
    """Metrics exporter for Microsoft Azure Monitor."""

    def __init__(self, options):
        self._options = options
        self._md_cache = {}
        self._md_lock = threading.Lock()

    def export_metrics(self, metrics):
        if metrics:
            metrics = list(metrics)
        envelopes = [self.metric_to_envelope(metric) for metric in metrics]
        self._transmit(envelopes)

    def metric_to_envelope(self, metric):
        envelope = Envelope(
            iKey=self.options.instrumentation_key,
            tags=dict(utils.azure_monitor_context),
            time=utils.timestamp_to_iso_str(time.time()),
        )
        envelope.name = 'Microsoft.ApplicationInsights.Metric'
        data = MetricData(
            namespace=metric.descriptor.name
            metrics=time_series_to_data_points(metric.time_series)
        )
        envelope.data = Data(baseData=data, baseType="MetricData")
        return envelope

    def time_series_to_data_points(self, time_series):
        """Convert an OC timeseries to a list of Azure data points."""
        data_points = []
        for points in time_series:



def new_metrics_exporter(**options):
    options = Options(**options)
    if not options.instrumentation_key:
        raise ValueError('The instrumentation_key is not provided.')
    exporter = MetricsExporter(options=options)
    transport.get_exporter_thread(stats.stats,
                                  exporter,
                                  interval=options.export_interval)
    return exporter
