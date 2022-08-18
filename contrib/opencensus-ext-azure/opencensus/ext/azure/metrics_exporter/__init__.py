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

import atexit

from opencensus.common import utils as common_utils
from opencensus.ext.azure.common import Options, utils
from opencensus.ext.azure.common.processor import ProcessorMixin
from opencensus.ext.azure.common.protocol import (
    Data,
    DataPoint,
    Envelope,
    MetricData,
)
from opencensus.ext.azure.common.storage import LocalFileStorage
from opencensus.ext.azure.common.transport import (
    TransportMixin,
    TransportStatusCode,
)
from opencensus.ext.azure.metrics_exporter import standard_metrics
from opencensus.ext.azure.statsbeat.statsbeat_metrics import (
    _NETWORK_STATSBEAT_NAMES,
)
from opencensus.metrics import transport
from opencensus.metrics.export.metric_descriptor import MetricDescriptorType
from opencensus.stats import stats as stats_module

__all__ = ['MetricsExporter', 'new_metrics_exporter']


class MetricsExporter(TransportMixin, ProcessorMixin):
    """Metrics exporter for Microsoft Azure Monitor."""

    def __init__(self, is_stats=False, **options):
        self.options = Options(**options)
        self._is_stats = is_stats
        utils.validate_instrumentation_key(self.options.instrumentation_key)
        if self.options.max_batch_size <= 0:
            raise ValueError('Max batch size must be at least 1.')
        self.export_interval = self.options.export_interval
        self.max_batch_size = self.options.max_batch_size
        self._telemetry_processors = []
        self.storage = None
        if self.options.enable_local_storage:
            self.storage = LocalFileStorage(
                path=self.options.storage_path,
                max_size=self.options.storage_max_size,
                maintenance_period=self.options.storage_maintenance_period,
                retention_period=self.options.storage_retention_period,
                source=self.__class__.__name__,
            )
        self._atexit_handler = atexit.register(self.shutdown)
        self.exporter_thread = None
        # For redirects
        self._consecutive_redirects = 0  # To prevent circular redirects
        super(MetricsExporter, self).__init__()

    def export_metrics(self, metrics):
        envelopes = []
        for metric in metrics:
            envelopes.extend(self.metric_to_envelopes(metric))
        # Send data in batches of max_batch_size
        batched_envelopes = list(common_utils.window(
            envelopes, self.max_batch_size))
        for batch in batched_envelopes:
            batch = self.apply_telemetry_processors(batch)
            result = self._transmit(batch)
            # If statsbeat exporter and received signal to shutdown
            if self._is_stats and result is \
                    TransportStatusCode.STATSBEAT_SHUTDOWN:
                from opencensus.ext.azure.statsbeat import statsbeat
                statsbeat.shutdown_statsbeat_metrics()
                return
            # Only store files if local storage enabled
            if self.storage:
                if result is TransportStatusCode.RETRY:
                    self.storage.put(batch, self.options.minimum_retry_interval)  # noqa: E501
                if result is TransportStatusCode.SUCCESS:
                    # If there is still room to transmit envelopes,
                    # transmit from storage if available
                    if len(envelopes) < self.options.max_batch_size:
                        self._transmit_from_storage()

    def metric_to_envelopes(self, metric):
        envelopes = []
        # No support for histogram aggregations
        if (metric.descriptor.type !=
                MetricDescriptorType.CUMULATIVE_DISTRIBUTION):
            md = metric.descriptor
            # Each time series will be uniquely identified by its
            # label values
            for time_series in metric.time_series:
                # time_series should only have one point which
                # contains the aggregated value
                # time_series point list is never empty
                point = time_series.points[0]
                # we ignore None and 0 values for network statsbeats
                if self._is_stats_exporter():
                    if md.name in _NETWORK_STATSBEAT_NAMES:
                        if not point.value.value:
                            continue
                data_point = DataPoint(
                    ns=md.name,
                    name=md.name,
                    value=point.value.value
                )
                # The timestamp is when the metric was recorded
                timestamp = point.timestamp
                # Get the properties using label keys from metric
                # and label values of the time series
                properties = self._create_properties(
                    time_series,
                    md.label_keys
                )
                envelopes.append(
                    self._create_envelope(
                        data_point,
                        timestamp,
                        properties
                    )
                )
        return envelopes

    def _create_properties(self, time_series, label_keys):
        properties = {}
        # We construct a properties map from the label keys and values. We
        # assume the ordering is already correct
        for i in range(len(label_keys)):
            if time_series.label_values[i].value is None:
                value = "null"
            else:
                value = time_series.label_values[i].value
            properties[label_keys[i].key] = value
        return properties

    def _create_envelope(self, data_point, timestamp, properties):
        envelope = Envelope(
            iKey=self.options.instrumentation_key,
            tags=dict(utils.azure_monitor_context),
            time=timestamp.isoformat(),
        )
        if self._is_stats:
            envelope.name = "Statsbeat"
        else:
            envelope.name = "Microsoft.ApplicationInsights.Metric"
        data = MetricData(
            metrics=[data_point],
            properties=properties
        )
        envelope.data = Data(baseData=data, baseType="MetricData")
        return envelope

    def shutdown(self):
        if self.exporter_thread:
            # flush if metrics exporter is not for stats
            if not self._is_stats:
                self.exporter_thread.close()
            else:
                self.exporter_thread.cancel()
        # Shutsdown storage worker
        if self.storage:
            self.storage.close()


def new_metrics_exporter(**options):
    exporter = MetricsExporter(**options)
    producers = [stats_module.stats]
    if exporter.options.enable_standard_metrics:
        producers.append(standard_metrics.producer)
    exporter.exporter_thread = transport.get_exporter_thread(
                                    producers,
                                    exporter,
                                    interval=exporter.options.export_interval)
    # start statsbeat on exporter instantiation
    if exporter._check_stats_collection():
        # Import here to avoid circular dependencies
        from opencensus.ext.azure.statsbeat import statsbeat
        statsbeat.collect_statsbeat_metrics(exporter.options)
    return exporter
