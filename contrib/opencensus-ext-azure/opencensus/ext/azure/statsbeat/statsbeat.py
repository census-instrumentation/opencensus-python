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
from opencensus.ext.azure.statsbeat.state import (
    _STATSBEAT_STATE,
    _STATSBEAT_STATE_LOCK,
)
from opencensus.ext.azure.statsbeat.statsbeat_metrics import (
    _STATS_SHORT_EXPORT_INTERVAL,
    _get_stats_connection_string,
    _StatsbeatMetrics,
)
from opencensus.metrics import transport
from opencensus.metrics.export.metric_producer import MetricProducer
from opencensus.trace import execution_context

_STATSBEAT_METRICS = None
_STATSBEAT_EXPORTER = None
_STATSBEAT_LOCK = threading.Lock()


def collect_statsbeat_metrics(options):
    # pylint: disable=global-statement
    global _STATSBEAT_METRICS
    global _STATSBEAT_EXPORTER
    # Only start statsbeat if did not exist before
    if _STATSBEAT_METRICS is None and _STATSBEAT_EXPORTER is None:
        with _STATSBEAT_LOCK:
            # Only start statsbeat if did not exist before
            exporter = MetricsExporter(
                is_stats=True,
                connection_string=_get_stats_connection_string(options.endpoint),  # noqa: E501
                enable_local_storage=options.enable_local_storage,
                enable_standard_metrics=False,
                export_interval=_STATS_SHORT_EXPORT_INTERVAL,  # 15m by default
            )
            # The user's ikey is the one being tracked
            producer = _AzureStatsbeatMetricsProducer(options)
            _STATSBEAT_METRICS = producer
            # Export some initial stats on program start
            execution_context.set_is_exporter(True)
            exporter.export_metrics(_STATSBEAT_METRICS.get_initial_metrics())
            execution_context.set_is_exporter(False)
            exporter.exporter_thread = \
                transport.get_exporter_thread([_STATSBEAT_METRICS],
                                              exporter,
                                              exporter.options.export_interval)
            _STATSBEAT_EXPORTER = exporter
        with _STATSBEAT_STATE_LOCK:
            _STATSBEAT_STATE["INITIAL_FAILURE_COUNT"] = 0
            _STATSBEAT_STATE["INITIAL_SUCCESS"] = 0
            _STATSBEAT_STATE["SHUTDOWN"] = False


def shutdown_statsbeat_metrics():
    # pylint: disable=global-statement
    global _STATSBEAT_METRICS
    global _STATSBEAT_EXPORTER
    shutdown_success = False
    if _STATSBEAT_METRICS is not None and _STATSBEAT_EXPORTER is not None and not _STATSBEAT_STATE["SHUTDOWN"]:  # noqa: E501
        with _STATSBEAT_LOCK:
            try:
                _STATSBEAT_EXPORTER.shutdown()
                _STATSBEAT_EXPORTER = None
                _STATSBEAT_METRICS = None
                shutdown_success = True
            except:  # pylint: disable=broad-except  # noqa: E722
                pass
        if shutdown_success:
            with _STATSBEAT_STATE_LOCK:
                _STATSBEAT_STATE["SHUTDOWN"] = True


class _AzureStatsbeatMetricsProducer(MetricProducer):
    """Implementation of the producer of statsbeat metrics.

    Includes Azure attach rate, network and feature metrics,
    implemented using gauges.
    """
    def __init__(self, options):
        self._statsbeat = _StatsbeatMetrics(options)

    def get_metrics(self):
        return self._statsbeat.get_metrics()

    def get_initial_metrics(self):
        return self._statsbeat.get_initial_metrics()
