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

from opencensus.common.transports import sync
from opencensus.ext.azure.protocol import Data
from opencensus.ext.azure.protocol import Envelope
from opencensus.ext.azure.protocol import Message
from opencensus.ext.azure.protocol import RemoteDependency
from opencensus.ext.azure.protocol import Request
from opencensus.ext.azure import utils
from opencensus.trace import base_exporter
from opencensus.trace import execution_context
from opencensus.trace.span import SpanKind


class AzureExporter(base_exporter.Exporter):
    """An exporter that sends traces to Microsoft Azure Monitor.

    :type config: dict
    :param config: Configuration for the exporter. Defaults to None.

    :type transport: :class:`type`
    :param transport: Class for creating new transport objects. It should
                      extend from the base_exporter :class:`.Transport` type
                      and implement :meth:`.Transport.export`. Defaults to
                      :class:`.SyncTransport`. The other option is
                      :class:`.AsyncTransport`.
    """

    def __init__(self, config=None, transport=sync.SyncTransport):
        self.config = config or utils.Config()
        self.transport = transport(self)

    def emit(self, span_datas):
        """
        :type span_datas: list of :class:
            `~opencensus.trace.span_data.SpanData`
        :param list of opencensus.trace.span_data.SpanData span_datas:
            SpanData tuples to emit
        """
        envelopes = []
        for sd in span_datas:
            start_time_us = utils.timestamp_to_microseconds(sd.start_time)
            end_time_us = utils.timestamp_to_microseconds(sd.end_time)
            duration_us = int(end_time_us - start_time_us)
            duration = utils.microseconds_to_duration(duration_us)

            print('[AzMon]', sd)
            print('trace_id:', sd.context.trace_id)
            print('tracestate:', sd.context.tracestate)
            print('span_id:', sd.span_id)
            print('parent_span_id:', sd.parent_span_id)
            print('attributes:', sd.attributes)
            print('start_time:', sd.start_time)
            print('end_time:', sd.end_time)

            envelope = Envelope(
                iKey=self.config.instrumentation_key,
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
                    duration=duration,
                    responseCode='0',  # TODO
                    success=True,  # TODO
                )
                envelope.data = Data(baseData=data, baseType='RequestData')
                if 'http.method' in sd.attributes:
                    data.name = sd.attributes['http.method']
                if 'http.url' in sd.attributes:
                    data.name = data.name + ' ' + sd.attributes['http.url']
                if 'http.status_code' in sd.attributes:
                    data.responseCode = sd.attributes['http.status_code']
            else:
                envelope.name = 'Microsoft.ApplicationInsights.RemoteDependency'
                data = RemoteDependency(
                    name=sd.name,  # TODO
                    id='|{}.{}.'.format(sd.context.trace_id, sd.span_id),
                    resultCode='0',  # TODO
                    duration=duration,
                    success=True,  # TODO
                )
                envelope.data = Data(baseData=data, baseType='RemoteDependencyData')
                if sd.span_kind == SpanKind.CLIENT:
                    data.type = 'HTTP'  # TODO
                    if 'http.url' in sd.attributes:
                        data.name = utils.urlparse(sd.attributes['http.url']).netloc  # TODO: error handling, probably put scheme as well (so that people can tell HTTP from HTTPS)
                    if 'http.status_code' in sd.attributes:
                        data.resultCode = sd.attributes['http.status_code']
                else:
                    envelope.data.type = 'IN PROCESS'
            # TODO: links, tracestate, tags, attrs
            print(json.dumps(envelope))
            envelopes.append(envelope)

        # TODO: prevent requests being tracked
        blacklist_hostnames = execution_context.get_opencensus_attr('blacklist_hostnames')
        execution_context.set_opencensus_attr('blacklist_hostnames', ['dc.services.visualstudio.com'])
        response = requests.post(
            url=self.config.endpoint,
            data=json.dumps(envelopes),
            headers={
                'Accept': 'application/json',
                'Content-Type': 'application/json; charset=utf-8',
            },
        )
        execution_context.set_opencensus_attr('blacklist_hostnames', blacklist_hostnames)
        print(response.status_code)
        print(response.json())

    def export(self, span_datas):
        """
        :type span_datas: list of :class:
            `~opencensus.trace.span_data.SpanData`
        :param list of opencensus.trace.span_data.SpanData span_datas:
            SpanData tuples to export
        """
        self.transport.export(span_datas)
