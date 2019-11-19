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

import requests

from opencensus.common import utils as common_utils
from opencensus.ext.azure.common import Options, utils
from opencensus.ext.azure.common.protocol import (
    Data,
    DataPoint,
    Envelope,
    MetricData,
)
from opencensus.ext.azure.metrics_exporter import standard_metrics
from opencensus.metrics import transport
from opencensus.metrics.export.metric_descriptor import MetricDescriptorType
from opencensus.stats import stats as stats_module

__all__ = ['MetricsExporter', 'new_metrics_exporter']

logger = logging.getLogger(__name__)


class MetricsExporter(object):
    """Metrics exporter for Microsoft Azure Monitor."""

    def __init__(self, options=None):
        if options is None:
            options = Options()
        self.options = options
        utils.validate_instrumentation_key(self.options.instrumentation_key)
        if self.options.max_batch_size <= 0:
            raise ValueError('Max batch size must be at least 1.')
        self.max_batch_size = self.options.max_batch_size

    def export_metrics(self, metrics):
        if metrics:
            envelopes = []
            for metric in metrics:
                # No support for histogram aggregations
                type_ = metric.descriptor.type
                if type_ != MetricDescriptorType.CUMULATIVE_DISTRIBUTION:
                    md = metric.descriptor
                    # Each time series will be uniquely identified by its
                    # label values
                    for time_series in metric.time_series:
                        # Using stats, time_series should only have one point
                        # which contains the aggregated value
                        data_point = self.create_data_points(
                            time_series, md)[0]
                        # The timestamp is when the metric was recorded
                        time_stamp = time_series.points[0].timestamp
                        # Get the properties using label keys from metric and
                        # label values of the time series
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
        # We construct a properties map from the label keys and values. We
        # assume the ordering is already correct
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
        # TODO: Remove this function from exporter and consolidate with
        # transport._transmit to cover all exporter use cases. Uses cases
        # pertain to properly handling failures and implementing a retry
        # policy for this exporter.
        # TODO: implement retry policy
        """
        Transmit the data envelopes to the ingestion service.
        Does not perform retry logic. For partial success and
        non-retryable failure, simply outputs result to logs.
        This function should never throw exception.
        """
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
                    # show the envelopes that can be retried manually for
                    # visibility
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
        # Check for non-retryable result
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


def new_metrics_exporter(**options):
    options_ = Options(**options)
    exporter = MetricsExporter(options=options_)
    producers = [stats_module.stats]
    if options_.enable_standard_metrics:
        producers.append(standard_metrics.producer)
    transport.get_exporter_thread(producers,
                                  exporter,
                                  interval=options_.export_interval)
    return exporter
