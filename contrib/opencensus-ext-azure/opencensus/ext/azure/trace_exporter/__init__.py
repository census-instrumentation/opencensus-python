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
from opencensus.ext.azure.common.exporter import BaseExporter
from opencensus.ext.azure.common.protocol import Data
from opencensus.ext.azure.common.protocol import Envelope
from opencensus.ext.azure.common.protocol import RemoteDependency
from opencensus.ext.azure.common.protocol import Request
from opencensus.ext.azure.common.storage import LocalFileStorage
from opencensus.trace import execution_context
from opencensus.trace.span import SpanKind

logger = logging.getLogger(__name__)

__all__ = ['AzureExporter']


class AzureExporter(BaseExporter):
    """An exporter that sends traces to Microsoft Azure Monitor.

    :type options: dict
    :param options: Options for the exporter. Defaults to None.
    """

    def __init__(self, **options):
        self.options = Options(**options)
        if not self.options.instrumentation_key:
            raise ValueError('The instrumentation_key is not provided.')
        self.storage = LocalFileStorage(
            path=self.options.storage_path,
            max_size=self.options.storage_max_size,
            maintenance_period=self.options.storage_maintenance_period,
            retention_period=self.options.storage_retention_period,
        )
        super(AzureExporter, self).__init__(**options)

    def span_data_to_envelope(self, sd):
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
        return envelope

    def _transmission_routine(self):
        for blob in self.storage.gets():
            if blob.lease(self.options.timeout + 5):
                envelopes = blob.get()  # TODO: handle error
                result = self._transmit(envelopes)
                if result > 0:
                    blob.lease(result)
                else:
                    blob.delete(silent=True)

    def _transmit(self, envelopes):
        """
        Transmit the data envelopes to the ingestion service.
        Return a negative value for partial success or non-retryable failure.
        Return 0 if all envelopes have been successfully ingested.
        Return the next retry time in seconds for retryable failure.
        This function should never throw exception.
        """
        if not envelopes:
            return 0
        # TODO: prevent requests being tracked
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
        except Exception as ex:  # TODO: consider RequestException
            logger.warning('Transient client side error %s.', ex)
            # client side error (retryable)
            return self.options.minimum_retry_interval
        finally:
            execution_context.set_opencensus_attr(
                'blacklist_hostnames',
                blacklist_hostnames,
            )
        text = 'N/A'
        data = None
        try:
            text = response.text
        except Exception as ex:
            logger.warning('Error while reading response body %s.', ex)
        else:
            try:
                data = json.loads(text)
            except Exception:
                pass
        if response.status_code == 200:
            logger.info('Transmission succeeded: %s.', text)
            return 0
        if response.status_code == 206:  # Partial Content
            # TODO: store the unsent data
            if data:
                try:
                    resend_envelopes = []
                    for error in data['errors']:
                        if error['statusCode'] in (
                                429,  # Too Many Requests
                                500,  # Internal Server Error
                                503,  # Service Unavailable
                        ):
                            resend_envelopes.append(envelopes[error['index']])
                        else:
                            logger.error(
                                'Data drop %s: %s %s.',
                                error['statusCode'],
                                error['message'],
                                envelopes[error['index']],
                            )
                    if resend_envelopes:
                        self.storage.put(resend_envelopes)
                except Exception as ex:
                    logger.error(
                        'Error while processing %s: %s %s.',
                        response.status_code,
                        text,
                        ex,
                    )
                return -response.status_code
            # cannot parse response body, fallback to retry
        if response.status_code in (
                206,  # Partial Content
                429,  # Too Many Requests
                500,  # Internal Server Error
                503,  # Service Unavailable
        ):
            logger.warning(
                'Transient server side error %s: %s.',
                response.status_code,
                text,
            )
            # server side error (retryable)
            return self.options.minimum_retry_interval
        logger.error(
            'Non-retryable server side error %s: %s.',
            response.status_code,
            text,
        )
        # server side error (non-retryable)
        return -response.status_code

    def emit(self, batch, event=None):
        if batch:
            envelopes = [self.span_data_to_envelope(sd) for sd in batch]
            result = self._transmit(envelopes)
            if result > 0:
                self.storage.put(envelopes, result)
        if event:
            if event is BaseExporter.EXIT_EVENT:
                self._transmission_routine()  # try to send files before exit
            event.set()
            return
        if not batch or len(batch) < self.options.max_batch_size:
            self._transmission_routine()
