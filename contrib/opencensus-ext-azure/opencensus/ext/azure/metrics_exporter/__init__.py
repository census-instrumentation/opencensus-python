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

import json
import logging
import psutil
import requests

from opencensus.common import utils as common_utils
from opencensus.ext.azure.common import Options
from opencensus.ext.azure.common import utils
from opencensus.ext.azure.common.protocol import Data
from opencensus.ext.azure.common.protocol import DataPoint
from opencensus.ext.azure.common.protocol import Envelope
from opencensus.ext.azure.common.protocol import MetricData
from opencensus.metrics import transport
from opencensus.metrics.export.metric_descriptor import MetricDescriptorType
from opencensus.stats import aggregation as aggregation_module
from opencensus.stats import measure as measure_module
from opencensus.stats import stats
from opencensus.stats import view as view_module
from opencensus.trace import execution_context

__all__ = ['MetricsExporter', 'new_metrics_exporter']

logger = logging.getLogger(__name__)


class MetricsExporter(object):
    """Metrics exporter for Microsoft Azure Monitor."""

    def __init__(self, options=None):
        if options is None:
            options = Options()
        self.options = options
        if not self.options.instrumentation_key:
            raise ValueError('The instrumentation_key is not provided.')
        if self.options.max_batch_size <= 0:
            raise ValueError('Max batch size must be at least 1.')
        self.max_batch_size = self.options.max_batch_size
        self.standard_metrics_map = {}
        self.standard_metrics_measure_map = {}

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
            if envelopes:
                batched_envelopes = list(common_utils.window(
                    envelopes, self.max_batch_size))
                for batch in batched_envelopes:
                    self._transmit_without_retry(batch)

    def create_data_points(self, time_series, metric_descriptor):
        """Convert a metric's OC time series to list of Azure data points."""
        data_points = []
        for point in time_series.points:
            # TODO: Possibly encode namespace in name
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
                value = "null"
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

    def _transmit_without_retry(self, envelopes):
        # Contains logic from transport._transmit
        # TODO: Remove this function from exporter and
        # consolidate with transport._transmit to cover
        # all exporter use cases.
        # Uses cases pertain to properly handling failures
        # and implementing a retry policy for this exporter
        # TODO: implement retry policy
        """
        Transmit the data envelopes to the ingestion service.
        Does not perform retry logic. For partial success and
        non-retryable failure, simply outputs result to logs.
        This function should never throw exception.
        """
        blacklist_hostnames = execution_context.get_opencensus_attr(
            'blacklist_hostnames',
        )
        execution_context.set_opencensus_attr(
            'blacklist_hostnames',
            ['dc.services.visualstudio.com'],
        )
        try:
            response = requests.post(
                url=self.options.endpoint,
                data=json.dumps(envelopes),
                headers={
                    'Accept': 'application/json',
                    'Content-Type': 'application/json; charset=utf-8',
                },
                timeout=self.options.timeout,
            )
        except Exception as ex:
            # No retry policy, log output
            logger.warning('Transient client side error %s.', ex)
            return
        finally:
            execution_context.set_opencensus_attr(
                'blacklist_hostnames',
                blacklist_hostnames,
            )

        text = 'N/A'
        data = None
        # Handle the possible results from the response
        if response is None:
            logger.warning('Error: cannot read response.')
            return
        try:
            status_code = response.status_code
        except Exception as ex:
            logger.warning('Error while reading response status code %s.', ex)
            return
        try:
            text = response.text
        except Exception as ex:
            logger.warning('Error while reading response body %s.', ex)
            return
        try:
            data = json.loads(text)
        except Exception as ex:
            logger.warning('Error while loading ' +
                           'json from response body %s.', ex)
            return
        if status_code == 200:
            logger.info('Transmission succeeded: %s.', text)
            return
        # Check for retryable partial content
        if status_code == 206:
            if data:
                try:
                    retryable_envelopes = []
                    for error in data['errors']:
                        if error['statusCode'] in (
                                429,  # Too Many Requests
                                500,  # Internal Server Error
                                503,  # Service Unavailable
                        ):
                            retryable_envelopes.append(
                                envelopes[error['index']])
                        else:
                            logger.error(
                                'Data drop %s: %s %s.',
                                error['statusCode'],
                                error['message'],
                                envelopes[error['index']],
                            )
                    # show the envelopes that can be
                    # retried manually for visibility
                    if retryable_envelopes:
                        logger.warning(
                            'Error while processing data. Data dropped. ' +
                            'Consider manually retrying for envelopes: %s.',
                            retryable_envelopes
                        )
                    return
                except Exception:
                    logger.exception(
                        'Error while processing %s: %s.',
                        status_code,
                        text
                    )
                    return
        # Check for non-tryable result
        if status_code in (
                206,  # Partial Content
                429,  # Too Many Requests
                500,  # Internal Server Error
                503,  # Service Unavailable
        ):
            # server side error (retryable)
            logger.warning(
                'Transient server side error %s: %s. ' +
                'Consider manually trying.',
                status_code,
                text,
            )
        else:
            # server side error (non-retryable)
            logger.error(
                'Non-retryable server side error %s: %s.',
                status_code,
                text,
            )

    def enable_standard_metrics(self):
        # Sets up stats related objects to begin
        # recording standard metrics
        stats_ = stats.stats
        view_manager = stats_.view_manager
        stats_recorder = stats_.stats_recorder

        # Standard metrics uses a separate instance of MeasurementMap
        # from regular metrics but still shares the same underlying
        # map data in the context. This way, the processing during
        # record is handled through a separate data structure but
        # the storage only uses one single data structure
        # Uniqueness should be based off the name of the view and
        # measure. A warning message in the logs will be shown
        # if there are duplicate names
        self.standard_metrics_map = stats_recorder.new_measurement_map()

        free_memory_measure = measure_module.MeasureInt("Free memory",
            "Amount of free memory in bytes",
            "bytes")
        self.standard_metrics_measure_map[StandardMetricType.FREE_MEMORY] = free_memory_measure
        free_memory_view = view_module.View(StandardMetricType.FREE_MEMORY,
            "Amount of free memory in bytes",
            [],
            free_memory_measure,
            aggregation_module.LastValueAggregation())
        view_manager.register_view(free_memory_view)

    def record_standard_metrics(self):
        # Function called periodically to record standard metrics
        vmem = psutil.virtual_memory()
        free_memory = vmem.free
        free_measure = self.standard_metrics_measure_map[StandardMetricType.FREE_MEMORY]
        if free_measure is not None:
            self.standard_metrics_map.measure_int_put(free_measure, free_memory)
        self.standard_metrics_map.record()


def new_metrics_exporter(**options):
    options_ = Options(**options)
    exporter = MetricsExporter(options=options_)
    if options_.enable_standard_metrics:
        exporter.enable_standard_metrics()
        transport.get_recorder_thread(exporter.record_standard_metrics,
                                      interval=options_.export_interval)
    transport.get_exporter_thread(stats.stats,
                                  exporter,
                                  interval=options_.export_interval)
    return exporter

class StandardMetricType(object):
    FREE_MEMORY = "\\Memory\\Available Bytes"
