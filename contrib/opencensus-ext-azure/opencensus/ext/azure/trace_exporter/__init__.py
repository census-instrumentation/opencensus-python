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
from opencensus.common import utils
from opencensus.ext.azure.protocol import Envelope
from opencensus.ext.azure.protocol import Message
from opencensus.ext.azure.protocol import RemoteDependency
from opencensus.ext.azure.protocol import Request
from opencensus.ext.azure.utils import azure_monitor_context
from opencensus.ext.azure.utils import microseconds_to_duration
from opencensus.trace import base_exporter
from opencensus.trace import execution_context
from opencensus.trace.span import SpanKind


class AzureExporter(base_exporter.Exporter):
    """An exporter that sends traces to Microsoft Azure Monitor.

    :type project_id: str
    :param project_id: project_id to create the Trace client.

    :type transport: :class:`type`
    :param transport: Class for creating new transport objects. It should
                      extend from the base_exporter :class:`.Transport` type
                      and implement :meth:`.Transport.export`. Defaults to
                      :class:`.SyncTransport`. The other option is
                      :class:`.AsyncTransport`.
    """

    def __init__(self, config=None, transport=sync.SyncTransport):
        self.config = config
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
            start_time_microseconds = utils.timestamp_to_microseconds(sd.start_time)
            end_time_microseconds = utils.timestamp_to_microseconds(sd.end_time)
            duration_microseconds = int(end_time_microseconds - start_time_microseconds)
            duration = microseconds_to_duration(duration_microseconds)

            print('[AzMon]', sd)
            print('trace_id:', sd.context.trace_id)
            print('tracestate:', sd.context.tracestate)
            print('span_id:', sd.span_id)
            print('parent_span_id:', sd.parent_span_id)
            print('attributes:', sd.attributes)
            print('start_time:', start_time_microseconds)
            print('end_time:', sd.end_time)
            print('span_kind:', sd.span_kind, {
                'CLIENT': SpanKind.CLIENT,
                'SERVER': SpanKind.SERVER,
            })
            print('duration(microseconds)', duration_microseconds)
            print('duration', duration)

            envelope = Envelope(
                iKey=self.config.instrumentation_key,
                tags=azure_monitor_context,
                time=sd.end_time,
            )
            if sd.span_kind == SpanKind.CLIENT:
                envelope.name = 'Microsoft.ApplicationInsights.RemoteDependency'
                envelope.data = {
                    'baseData': RemoteDependency(
                        name='GET /foobarbaz',  # TODO
                        id='!{}.{}'.format(sd.context.trace_id, sd.span_id),  # TODO
                        resultCode='200',  # TODO
                        duration=duration,
                        success=True,  # TODO
                    ),
                    'baseType': 'RemoteDependencyData',
                }
            elif sd.span_kind == SpanKind.SERVER:
                envelope.name = 'Microsoft.ApplicationInsights.Request'
                envelope.data = {
                    'baseData': Request(
                        id='!{}.{}'.format(sd.context.trace_id, sd.span_id),  # TODO
                        duration=duration,
                        responseCode='200',  # TODO
                        success=True,  # TODO
                    ),
                    'baseType': 'RequestData',
                }
            else:  # unknown
                envelope.name = 'Microsoft.ApplicationInsights.Message'
                envelope.data = {
                    'baseData': Message(message=str(sd)),
                    'baseType': 'MessageData',
                }
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
