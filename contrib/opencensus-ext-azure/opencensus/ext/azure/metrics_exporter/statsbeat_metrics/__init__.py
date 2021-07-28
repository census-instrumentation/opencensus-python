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
from opencensus.ext.azure.metrics_exporter.statsbeat_metrics.statsbeat import (
    _StatsbeatMetrics,
)
from opencensus.metrics import transport
from opencensus.metrics.export.metric_producer import MetricProducer

_STATSBEAT_METRICS = None
_STATSBEAT_LOCK = threading.Lock()


def enable_statsbeat_metrics(connection_string, ikey):
    with _STATSBEAT_LOCK:
        # Only start statsbeat if did not exist before
        global _STATSBEAT_METRICS  # pylint: disable=global-statement
        if _STATSBEAT_METRICS is None:
            exporter = MetricsExporter(
                is_stats=True,
                connection_string=connection_string,
                instrumentation_key=ikey,
                export_interval=5.0,  # Send every 15 minutes
            )
            producer = _AzureStatsbeatMetricsProducer(
                instrumentation_key = exporter.options.instrumentation_key
            )
            _STATSBEAT_METRICS = producer
            exporter.exporter_thread = \
                transport.get_exporter_thread([_STATSBEAT_METRICS],
                                              exporter,
                                              exporter.options.export_interval)


class _AzureStatsbeatMetricsProducer(MetricProducer):
    """Implementation of the producer of statsbeat metrics.

    Includes Azure attach rate metrics, implemented using gauges.
    """
    def __init__(self, instrumentation_key):
        self._statsbeat = _StatsbeatMetrics(instrumentation_key)

    def get_metrics(self):
        return self._statsbeat.get_metrics()
