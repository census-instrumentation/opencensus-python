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
import json
import logging

from opencensus.common.schedule import QueueExitEvent
from opencensus.ext.azure.common import Options, utils
from opencensus.ext.azure.common.exporter import BaseExporter
from opencensus.ext.azure.common.processor import ProcessorMixin
from opencensus.ext.azure.common.protocol import (
    Data,
    Envelope,
    ExceptionData,
    RemoteDependency,
    Request,
)
from opencensus.ext.azure.common.storage import LocalFileStorage
from opencensus.ext.azure.common.transport import (
    TransportMixin,
    TransportStatusCode,
)
from opencensus.ext.azure.statsbeat import statsbeat
from opencensus.trace import attributes_helper
from opencensus.trace.span import SpanKind

try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse

logger = logging.getLogger(__name__)

__all__ = ['AzureExporter']

HTTP_METHOD = attributes_helper.COMMON_ATTRIBUTES['HTTP_METHOD']
HTTP_PATH = attributes_helper.COMMON_ATTRIBUTES['HTTP_PATH']
HTTP_ROUTE = attributes_helper.COMMON_ATTRIBUTES['HTTP_ROUTE']
HTTP_URL = attributes_helper.COMMON_ATTRIBUTES['HTTP_URL']
HTTP_STATUS_CODE = attributes_helper.COMMON_ATTRIBUTES['HTTP_STATUS_CODE']
ERROR_MESSAGE = attributes_helper.COMMON_ATTRIBUTES['ERROR_MESSAGE']
ERROR_NAME = attributes_helper.COMMON_ATTRIBUTES['ERROR_NAME']
STACKTRACE = attributes_helper.COMMON_ATTRIBUTES['STACKTRACE']


class AzureExporter(BaseExporter, TransportMixin, ProcessorMixin):
    """An exporter that sends traces to Microsoft Azure Monitor.

    :param options: Options for the exporter.
    """

    def __init__(self, **options):
        super(AzureExporter, self).__init__(**options)
        self.options = Options(**options)
        utils.validate_instrumentation_key(self.options.instrumentation_key)
        self.storage = None
        if self.options.enable_local_storage:
            self.storage = LocalFileStorage(
                path=self.options.storage_path,
                max_size=self.options.storage_max_size,
                maintenance_period=self.options.storage_maintenance_period,
                retention_period=self.options.storage_retention_period,
                source=self.__class__.__name__,
            )
        self._telemetry_processors = []
        atexit.register(self._stop, self.options.grace_period)
        # start statsbeat on exporter instantiation
        if self._check_stats_collection():
            statsbeat.collect_statsbeat_metrics(self.options)
        # For redirects
        self._consecutive_redirects = 0  # To prevent circular redirects

    def span_data_to_envelope(self, sd):
        envelope = Envelope(
            iKey=self.options.instrumentation_key,
            tags=dict(utils.azure_monitor_context),
            time=sd.start_time,
        )

        envelope.tags['ai.operation.id'] = sd.context.trace_id
        if sd.parent_span_id:
            envelope.tags['ai.operation.parentId'] = '{}'.format(
                sd.parent_span_id,
            )
        if sd.span_kind == SpanKind.SERVER:
            if ERROR_MESSAGE in sd.attributes:
                exc_env = Envelope(**envelope)
                exc_env.name = 'Microsoft.ApplicationInsights.Exception'
                data = ExceptionData(
                    exceptions=[{
                        'id': 1,
                        'outerId': '{}'.format(sd.span_id),
                        'typeName': sd.attributes.get(ERROR_NAME, ''),
                        'message': sd.attributes[ERROR_MESSAGE],
                        'hasFullStack': STACKTRACE in sd.attributes,
                        'parsedStack': sd.attributes.get(STACKTRACE, None)
                    }],
                )
                exc_env.data = Data(baseData=data, baseType='ExceptionData')
                yield exc_env

            envelope.name = 'Microsoft.ApplicationInsights.Request'
            data = Request(
                id='{}'.format(sd.span_id),
                duration=utils.timestamp_to_duration(
                    sd.start_time,
                    sd.end_time,
                ),
                responseCode=str(sd.status.code),
                success=False,  # Modify based off attributes or status
                properties={},
            )
            envelope.data = Data(baseData=data, baseType='RequestData')
            data.name = ''
            if HTTP_METHOD in sd.attributes:
                data.name = sd.attributes[HTTP_METHOD]
            if HTTP_ROUTE in sd.attributes:
                data.name = data.name + ' ' + sd.attributes[HTTP_ROUTE]
                envelope.tags['ai.operation.name'] = data.name
                data.properties['request.name'] = data.name
            elif HTTP_PATH in sd.attributes:
                data.properties['request.name'] = data.name + \
                    ' ' + sd.attributes[HTTP_PATH]
            if HTTP_URL in sd.attributes:
                data.url = sd.attributes[HTTP_URL]
                data.properties['request.url'] = sd.attributes[HTTP_URL]
            if HTTP_STATUS_CODE in sd.attributes:
                status_code = sd.attributes[HTTP_STATUS_CODE]
                data.responseCode = str(status_code)
                data.success = (
                    status_code >= 200 and status_code <= 399
                )
            elif sd.status.code == 0:
                data.success = True
        else:
            envelope.name = \
                'Microsoft.ApplicationInsights.RemoteDependency'
            data = RemoteDependency(
                name=sd.name,  # TODO
                id='{}'.format(sd.span_id),
                resultCode=str(sd.status.code),
                duration=utils.timestamp_to_duration(
                    sd.start_time,
                    sd.end_time,
                ),
                success=False,  # Modify based off attributes or status
                properties={},
            )
            envelope.data = Data(
                baseData=data,
                baseType='RemoteDependencyData',
            )
            if sd.span_kind == SpanKind.CLIENT:
                data.type = sd.attributes.get('component')
                if HTTP_URL in sd.attributes:
                    url = sd.attributes[HTTP_URL]
                    # TODO: error handling, probably put scheme as well
                    data.data = url
                    parse_url = urlparse(url)
                    # target matches authority (host:port)
                    data.target = parse_url.netloc
                    if HTTP_METHOD in sd.attributes:
                        # name is METHOD/path
                        data.name = sd.attributes[HTTP_METHOD] \
                            + ' ' + parse_url.path
                if HTTP_STATUS_CODE in sd.attributes:
                    status_code = sd.attributes[HTTP_STATUS_CODE]
                    data.resultCode = str(status_code)
                    data.success = 200 <= status_code < 400
                elif sd.status.code == 0:
                    data.success = True
            else:
                data.type = 'INPROC'
                data.success = True
        if sd.links:
            links = []
            for link in sd.links:
                links.append(
                    {"operation_Id": link.trace_id, "id": link.span_id})
            data.properties["_MS.links"] = json.dumps(links)
        # TODO: tracestate, tags
        for key in sd.attributes:
            # This removes redundant data from ApplicationInsights
            if key.startswith('http.'):
                continue
            data.properties[key] = sd.attributes[key]
        yield envelope

    def emit(self, batch, event=None):
        try:
            if batch:
                envelopes = [envelope
                             for sd in batch
                             for envelope in self.span_data_to_envelope(sd)]
                envelopes = self.apply_telemetry_processors(envelopes)
                result = self._transmit(envelopes)
                # Only store files if local storage enabled
                if self.storage and result is TransportStatusCode.RETRY:
                    self.storage.put(
                        envelopes,
                        self.options.minimum_retry_interval
                    )
            if event:
                if self.storage and isinstance(event, QueueExitEvent):
                    self._transmit_from_storage()  # send files before exit
                event.set()
                return
            if self.storage and len(batch) < self.options.max_batch_size:
                self._transmit_from_storage()
        except Exception:
            logger.exception('Exception occurred while exporting the data.')

    def _stop(self, timeout=None):
        if self.storage:
            self.storage.close()
        if self._worker:
            self._worker.stop(timeout)
