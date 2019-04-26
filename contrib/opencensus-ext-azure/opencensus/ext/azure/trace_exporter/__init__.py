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
import requests

from opencensus.common.transports.async_ import AsyncTransport
from opencensus.ext.azure.common import Options
from opencensus.ext.azure.common import utils
from opencensus.ext.azure.common.protocol import Data
from opencensus.ext.azure.common.protocol import Envelope
from opencensus.ext.azure.common.protocol import RemoteDependency
from opencensus.ext.azure.common.protocol import Request
from opencensus.ext.azure.common.storage import LocalFileStorage
from opencensus.trace import base_exporter
from opencensus.trace import execution_context
from opencensus.trace.span import SpanKind

__all__ = ['AzureExporter']


class AzureExporter(base_exporter.Exporter):
    """An exporter that sends traces to Microsoft Azure Monitor.

    :type options: dict
    :param options: Options for the exporter. Defaults to None.
    """

    def __init__(self, options=None):
        self.options = options or Options()
        self.storage = LocalFileStorage('.azure', maintenance_period=5)
        self.transport = AsyncTransport(self, max_batch_size=100)

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

    def transmit(self, envelopes):
        """
        Transmit the data envelopes to the ingestion service.
        Return the number of envelopes that has been ingested.
        This function should never throw exception, the unsent envelopes will
        be persisted on local file system.
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
            if response.status_code == 200:  # HTTP OK
                return len(envelopes)
            if response.status_code == 206:  # HTTP Partial Content
                # TODO: store the unsent data
                return len(envelopes)
            if response.status_code == 400:  # HTTP Bad Request
                return 0  # TODO: log data loss, don't retry
            if response.status_code == 402:  # HTTP Payment Required
                # store data, retry an hour later
                blob = self.storage.put(envelopes, 3600)
                return 0
            if response.status_code == 429:  # HTTP Too Many Requests
                # TODO: determine when to retry based on the retry policy
                blob = self.storage.put(envelopes, 5 * 60)
                return 0
            if response.status_code == 500:  # HTTP Internal Server Error
                # store data, retry 5 minutes later
                blob = self.storage.put(envelopes, 5 * 60)
                return 0
            if response.status_code == 503:  # HTTP Service Unavailable
                # TODO: determine when to retry based on the retry policy
                blob = self.storage.put(envelopes, 5 * 60)
                return 0
            # TODO: log unknown HTTP status code
            return 0
        except Exception:
            self.storage.put(envelopes, 60)
            return 0

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
        self.transmit(envelopes)
        execution_context.set_opencensus_attr(
            'blacklist_hostnames',
            blacklist_hostnames,
        )

    def export(self, span_datas):
        """
        :type span_datas: list of :class:
            `~opencensus.trace.span_data.SpanData`
        :param list of opencensus.trace.span_data.SpanData span_datas:
            SpanData tuples to export
        """
        self.transport.export(span_datas)
