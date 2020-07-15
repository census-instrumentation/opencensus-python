# Copyright 2020, OpenCensus Authors
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

from opencensus.ext.azure.metrics_exporter import MetricsExporter
from opencensus.ext.azure.metrics_exporter.heartbeat_metrics.heartbeat import HeartbeatMetric
from opencensus.metrics import transport
from opencensus.metrics.export.gauge import Registry
from opencensus.metrics.export.metric_producer import MetricProducer

_HEARTBEAT_METRICS = None
_HEARTBEAT_LOCK = threading.Lock()

def enable_heartbeat_metrics(connection_string, ikey):
    with _HEARTBEAT_LOCK:
        # Only start heartbeat if did not exist before
        global _HEARTBEAT_METRICS  # pylint: disable=global-statement
        if _HEARTBEAT_METRICS is None:
            exporter = MetricsExporter(
                connection_string=connection_string,
                instrumentation_key=ikey,
                export_interval=2
            )
            producer = AzureHeartbeatMetricsProducer()
            _HEARTBEAT_METRICS = producer
            transport.get_exporter_thread([_HEARTBEAT_METRICS],
                                          exporter,
                                          exporter.options.export_interval)

def register_metrics():
    registry = Registry()
    metric = HeartbeatMetric()
    registry.add_gauge(metric())
    return registry


class AzureHeartbeatMetricsProducer(MetricProducer):
    """Implementation of the producer of heartbeat metrics.

    Includes Azure attach rate metrics, implemented using gauges.
    """
    def __init__(self):
        self.registry = register_metrics()

    def get_metrics(self):
        return self.registry.get_metrics()
