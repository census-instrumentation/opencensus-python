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

from opencensus.common.transports import sync
from opencensus.common import utils
# from opencensus.ext.azure.protocol import Request
from opencensus.trace import base_exporter
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
        for sd in span_datas:
            start_time_microseconds = utils.timestamp_to_microseconds(sd.start_time)
            end_time_microseconds = utils.timestamp_to_microseconds(sd.end_time)
            duration_microseconds = int(end_time_microseconds - start_time_microseconds)

            n = (duration_microseconds + 500) // 1000  # duration in milliseconds
            ms = n % 1000  # millisecond
            n = n // 1000
            s = n % 60  # second
            n = n // 60
            m = n % 60  # minute
            n = n // 60
            h = n % 24  # hour
            d = n // 24  # day
            duration = '{:02d}:{:02d}:{:02d}.{:03d}'.format(h, m, s, ms)
            if d:
                duration = str(d) + '.' + duration

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

    def export(self, span_datas):
        """
        :type span_datas: list of :class:
            `~opencensus.trace.span_data.SpanData`
        :param list of opencensus.trace.span_data.SpanData span_datas:
            SpanData tuples to export
        """
        self.transport.export(span_datas)
