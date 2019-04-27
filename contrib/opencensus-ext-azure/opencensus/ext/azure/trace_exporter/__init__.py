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

import logging
import json
import requests

from opencensus.common.transports.async_ import AsyncTransport
from opencensus.ext.azure.common import Options
from opencensus.ext.azure.common import utils
from opencensus.ext.azure.common.schedule import PeriodicTask
from opencensus.ext.azure.common.protocol import Data
from opencensus.ext.azure.common.protocol import Envelope
from opencensus.ext.azure.common.protocol import RemoteDependency
from opencensus.ext.azure.common.protocol import Request
from opencensus.ext.azure.common.storage import LocalFileStorage
from opencensus.trace import base_exporter
from opencensus.trace import execution_context
from opencensus.trace.span import SpanKind

logger = logging.getLogger(__name__)

__all__ = ['AzureExporter']


class AzureExporter(base_exporter.Exporter):
    """An exporter that sends traces to Microsoft Azure Monitor.

    :type options: dict
    :param options: Options for the exporter. Defaults to None.
    """

    def __init__(self, options=None):
        self.options = options or Options()
        if not self.options.instrumentation_key:
            raise ValueError('The instrumentation_key is not provided.')
        self.storage = LocalFileStorage(
            self.options.storage_path,
            maintenance_period=self.options.storage_maintenance_period,
        )
        self.transport = AsyncTransport(self, max_batch_size=100)
        self._transmission_task = PeriodicTask(
            interval=self.options.storage_maintenance_period,
            function=self._transmission_routine,
        )
        self._transmission_task.start()

    def span_data_to_envelope(self, sd):
        # print('[AzMon]', sd)
        # print('attributes:', sd.attributes)
        envelope = Envelope(
            iKey=self.options.instrumentation_key,
            tags=dict(utils.azure_monitor_context),
            time=sd.start_time,
        )
        envelope.tags['ai.operation.id'] = sd.context.trace_id
        if sd.parent_span_id:
            envelope.tags['ai.operation.parentId'] = '|{}.{}.'.format(
                sd.context.trace_id,
                sd.parent_span_id,
            )
        if sd.span_kind == SpanKind.SERVER:
            envelope.name = 'Microsoft.ApplicationInsights.Request'
            data = Request(
                id='|{}.{}.'.format(sd.context.trace_id, sd.span_id),
                duration=utils.timestamp_to_duration(
                    sd.start_time,
                    sd.end_time,
                ),
                responseCode='0',  # TODO
                success=True,  # TODO
            )
            envelope.data = Data(baseData=data, baseType='RequestData')
            if 'http.method' in sd.attributes:
                data.name = sd.attributes['http.method']
            if 'http.url' in sd.attributes:
                data.name = data.name + ' ' + sd.attributes['http.url']
                data.url = sd.attributes['http.url']
            if 'http.status_code' in sd.attributes:
                data.responseCode = str(sd.attributes['http.status_code'])
        else:
            envelope.name = \
                'Microsoft.ApplicationInsights.RemoteDependency'
            data = RemoteDependency(
                name=sd.name,  # TODO
                id='|{}.{}.'.format(sd.context.trace_id, sd.span_id),
                resultCode='0',  # TODO
                duration=utils.timestamp_to_duration(
                    sd.start_time,
                    sd.end_time,
                ),
                success=True,  # TODO
            )
            envelope.data = Data(
                baseData=data,
                baseType='RemoteDependencyData',
            )
            if sd.span_kind == SpanKind.CLIENT:
                data.type = 'HTTP'  # TODO
                if 'http.url' in sd.attributes:
                    url = sd.attributes['http.url']
                    # TODO: error handling, probably put scheme as well
                    data.name = utils.url_to_dependency_name(url)
                if 'http.status_code' in sd.attributes:
                    data.resultCode = str(sd.attributes['http.status_code'])
            else:
                data.type = 'INPROC'
        # TODO: links, tracestate, tags, attrs
        # print(json.dumps(envelope))
        return envelope

    def _transmission_routine(self):
        for blob in self.storage.gets():
            if blob.lease(self.options.timeout + 5):
                envelopes = blob.get()  # TODO: handle error
                result = self._transmit(envelopes)
                if result > 0:
                    blob.lease(result)
                blob.delete(silent=True)

    def _transmit(self, envelopes):
        """
        Transmit the data envelopes to the ingestion service.
        Return a negative value for partial success or non-retryable failure.
        Return 0 if all envelopes have been successfully ingested.
        Return the next retry time in seconds for retryable failure.
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
            logger.warning('Transient client side error {}.'.format(ex))
            # client side error (retryable)
            return self.options.minimum_retry_interval
        text = 'N/A'
        try:
            text = response.text
        except Exception as ex:
            logger.warning('Error while reading response body {}.'.format(ex))
        if response.status_code == 200:
            logger.info('Transmission succeeded: {}.'.format(text))
            return 0
        if response.status_code == 206:  # Partial Content
            # TODO: store the unsent data
            return -response.status_code
        if response.status_code in (
            402,  # Payment Required
            429,  # Too Many Requests
            500,  # Internal Server Error
            503,  # Service Unavailable
        ):
            logger.warning('Transient server side error {}: {}.'.format(
                response.status_code,
                text,
            ))
            # server side error (retryable)
            return self.options.minimum_retry_interval
        logger.error('Non-retryable server side error {}: {}.'.format(
            response.status_code,
            text,
        ))
        # server side error (non-retryable)
        return -response.status_code

    def emit(self, span_datas):
        """
        :type span_datas: list of :class:
            `~opencensus.trace.span_data.SpanData`
        :param list of opencensus.trace.span_data.SpanData span_datas:
            SpanData tuples to emit
        """
        envelopes = [self.span_data_to_envelope(sd) for sd in span_datas]

        # TODO: prevent requests being tracked
        blacklist_hostnames = execution_context.get_opencensus_attr(
            'blacklist_hostnames',
        )
        execution_context.set_opencensus_attr(
            'blacklist_hostnames',
            ['dc.services.visualstudio.com'],
        )
        result = self._transmit(envelopes)
        execution_context.set_opencensus_attr(
            'blacklist_hostnames',
            blacklist_hostnames,
        )
        if result > 0:
            self.storage.put(envelopes, result)

    def export(self, span_datas):
        """
        :type span_datas: list of :class:
            `~opencensus.trace.span_data.SpanData`
        :param list of opencensus.trace.span_data.SpanData span_datas:
            SpanData tuples to export
        """
        self.transport.export(span_datas)
