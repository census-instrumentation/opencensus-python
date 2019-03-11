# Copyright 2018, OpenCensus Authors
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

"""Export the spans data to Jaeger."""

import logging
import socket

from thrift.protocol import TBinaryProtocol, TCompactProtocol
from thrift.transport import THttpClient, TTransport

from opencensus.common.transports import sync
from opencensus.common.utils import timestamp_to_microseconds
from opencensus.ext.jaeger.trace_exporter.gen.jaeger import agent, jaeger
from opencensus.trace import base_exporter
from opencensus.trace import link as link_module

DEFAULT_HOST_NAME = 'localhost'
DEFAULT_AGENT_PORT = 6831
DEFAULT_ENDPOINT = '/api/traces?format=jaeger.thrift'

UDP_PACKET_MAX_LENGTH = 65000

logging = logging.getLogger(__name__)


class JaegerExporter(base_exporter.Exporter):
    """Exports the spans to Jaeger.

    :type service_name: str
    :param service_name: Service that logged an annotation in a trace.
                         Classifier when query for spans.

    :type host_name: str
    :param host_name: (Optional) The host name of the Jaeger HTTP Thrift.

    :type port: int
    :param port: (Optional) The port of the Jaeger HTTP Thrift.

    :type username: str
    :param username: (Optional) The user name of the Basic Auth
                     if authentication is required.

    :type password: str
    :param password: (Optional) The password of the Basic Auth
                     if authentication is required.

    :type endpoint: str
    :param port: (Optional) The endpoint of the Jaeger HTTP Thrift .

    :type agent_host_name: str
    :param agent_host_name: (Optional) The host name of the Jaeger-Agent.

    :type agent_port: int
    :param agent_port: (Optional) The port of the Jaeger-Agent.


    :type transport: :class:`type`
    :param transport: Class for creating new transport objects. It should
                      extend from the base_exporter :class:`.Transport` type
                      and implement :meth:`.Transport.export`. Defaults to
                      :class:`.SyncTransport`. The other option is
                      :class:`.AsyncTransport`.
    """

    def __init__(
            self,
            service_name='my_service',
            host_name=None,
            port=None,
            username=None,
            password=None,
            endpoint='',
            agent_host_name=DEFAULT_HOST_NAME,
            agent_port=DEFAULT_AGENT_PORT,
            agent_endpoint=DEFAULT_ENDPOINT,
            transport=sync.SyncTransport):
        self.transport = transport(self)
        self.service_name = service_name
        self.host_name = host_name
        self.agent_host_name = agent_host_name
        self.port = port
        self.agent_port = agent_port
        self.endpoint = endpoint
        self.username = username
        self.password = password
        self._agent_client = None
        self._collector = None

    @property
    def agent_client(self):
        if self._agent_client is None:
            self._agent_client = AgentClientUDP(
                host_name=self.agent_host_name,
                port=self.agent_port)
        return self._agent_client

    @property
    def collector(self):
        if self._collector is not None:
            return self._collector

        if self.host_name is None or self.port is None:
            return None

        thrift_url = 'http://{}:{}{}'.format(
            self.host_name,
            self.port,
            self.endpoint or DEFAULT_ENDPOINT)

        auth = None
        if self.username is not None and self.password is not None:
            auth = (self.username, self.password)

        self._collector = Collector(
            thrift_url=thrift_url, auth=auth)
        return self._collector

    def emit(self, span_datas):
        """
        :type span_datas: list of :class:
            `~opencensus.trace.span_data.SpanData`
        :param span_datas:
            SpanData tuples to emit
        """
        jaeger_spans = self.translate_to_jaeger(span_datas)

        batch = jaeger.Batch(
            spans=jaeger_spans,
            process=jaeger.Process(serviceName=self.service_name))

        if self.collector is not None:
            self.collector.export(batch)
        self.agent_client.export(batch)

    def export(self, span_datas):
        """Export the trace. Send trace to transport, and transport will call
        exporter.emit() to actually send the trace to the specified tracing
        backend.

        :type span_datas: list of :class:
            `~opencensus.trace.span_data.SpanData`
        :param span_datas:
            SpanData tuples to export
        """
        self.transport.export(span_datas)

    def translate_to_jaeger(self, span_datas):
        """Translate the spans to Jaeger format.

        :type span_datas: list of :class:
            `~opencensus.trace.span_data.SpanData`
        :param span_datas:
            SpanData tuples to emit
        """

        top_span = span_datas[0]

        trace_id = top_span.context.trace_id if top_span.context is not None \
            else None

        jaeger_spans = []

        for span in span_datas:
            start_timestamp_ms = timestamp_to_microseconds(span.start_time)
            end_timestamp_ms = timestamp_to_microseconds(span.end_time)
            duration_ms = end_timestamp_ms - start_timestamp_ms

            tags = _extract_tags(span.attributes)

            status = span.status
            if status is not None:
                tags.append(jaeger.Tag(
                    key='status.code',
                    vType=jaeger.TagType.LONG,
                    vLong=status.code))

                tags.append(jaeger.Tag(
                    key='status.message',
                    vType=jaeger.TagType.STRING,
                    vStr=status.message))

            refs = _extract_refs_from_span(span)
            logs = _extract_logs_from_span(span)

            context = span.context
            flags = None
            if context is not None:
                flags = int(context.trace_options.trace_options_byte)

            span_id = span.span_id
            parent_span_id = span.parent_span_id

            jaeger_span = jaeger.Span(
                traceIdHigh=_convert_hex_str_to_int(trace_id[0:16]),
                traceIdLow=_convert_hex_str_to_int(trace_id[16:32]),
                spanId=_convert_hex_str_to_int(span_id),
                operationName=span.name,
                startTime=int(round(start_timestamp_ms)),
                duration=int(round(duration_ms)),
                tags=tags,
                logs=logs,
                references=refs,
                flags=flags,
                parentSpanId=_convert_hex_str_to_int(parent_span_id or '0'))

            jaeger_spans.append(jaeger_span)

        return jaeger_spans


def _extract_refs_from_span(span):
    if span.links is None:
        return None

    refs = []
    for link in span.links:
        trace_id = link.trace_id
        refs.append(jaeger.SpanRef(
            refType=_convert_reftype_to_jaeger_reftype(link.type),
            traceIdHigh=_convert_hex_str_to_int(trace_id[0:16]),
            traceIdLow=_convert_hex_str_to_int(trace_id[16:32]),
            spanId=_convert_hex_str_to_int(link.span_id)))
    return refs


def _convert_reftype_to_jaeger_reftype(ref):
    """Convert opencensus reference types to jaeger reference types."""
    if ref == link_module.Type.CHILD_LINKED_SPAN:
        return jaeger.SpanRefType.CHILD_OF
    if ref == link_module.Type.PARENT_LINKED_SPAN:
        return jaeger.SpanRefType.FOLLOWS_FROM
    return None


def _convert_hex_str_to_int(val):
    """Convert hexadecimal formatted ids to signed int64"""
    if val is None:
        return None

    hex_num = int(val, 16)
    #  ensure it fits into 64-bit
    if hex_num > 0x7FFFFFFFFFFFFFFF:
        hex_num -= 0x10000000000000000

    assert -9223372036854775808 <= hex_num <= 9223372036854775807
    return hex_num


def _extract_logs_from_span(span):
    if span.time_events is None:
        return None

    logs = []
    for time_event in span.time_events:
        annotation = time_event.annotation
        if not annotation:
            continue

        fields = []
        if annotation.attributes is not None:
            fields = _extract_tags(annotation.attributes.attributes)

        fields.append(jaeger.Tag(
            key='message',
            vType=jaeger.TagType.STRING,
            vStr=annotation.description))

        event_timestamp = timestamp_to_microseconds(time_event.timestamp)
        logs.append(jaeger.Log(timestamp=int(round(event_timestamp)),
                               fields=fields))
    return logs


def _extract_tags(attr):
    if attr is None:
        return []
    tags = []
    for attribute_key, attribute_value in attr.items():
        tag = _convert_attribute_to_tag(attribute_key, attribute_value)
        if tag is None:
            continue
        tags.append(tag)
    return tags


def _convert_attribute_to_tag(key, attr):
    """Convert the attributes to jaeger tags."""
    if isinstance(attr, bool):
        return jaeger.Tag(
            key=key,
            vBool=attr,
            vType=jaeger.TagType.BOOL)
    if isinstance(attr, str):
        return jaeger.Tag(
            key=key,
            vStr=attr,
            vType=jaeger.TagType.STRING)
    if isinstance(attr, int):
        return jaeger.Tag(
            key=key,
            vLong=attr,
            vType=jaeger.TagType.LONG)
    if isinstance(attr, float):
        return jaeger.Tag(
            key=key,
            vDouble=attr,
            vType=jaeger.TagType.DOUBLE)
    logging.warn('Could not serialize attribute \
            {}:{} to tag'.format(key, attr))
    return None


class Collector(base_exporter.Exporter):
    """Submits collected spans to Thrift HTTP server.

    :type thrift_url: str
    :param thrift_url: URL of the Jaeger HTTP Thrift.

    :type auth: tupple
    :param auth: (Optional) Auth tupple that contains username and
                password for Basic Auth.

    :type transport: :class:`type`
    :param transport: Class for creating new transport objects. It should
                      extend from the base_exporter :class:`.Transport` type
                      and implement :meth:`.Transport.export`. Defaults to
                      :class:`.SyncTransport`. The other option is
                      :class:`.AsyncTransport`.

    :type http_transport: :class:`type`
    :param http_transport: Class for creating new client for Thrift
                           HTTP server.
    """

    def __init__(
            self,
            thrift_url='',
            auth=None,
            client=jaeger.Client,
            transport=sync.SyncTransport,
            http_transport=THttpClient.THttpClient):
        self.transport = transport(self)
        self.thrift_url = thrift_url
        self.auth = auth
        self.http_transport = http_transport(uri_or_host=thrift_url)
        self.client = client(
            iprot=TBinaryProtocol.TBinaryProtocol(trans=self.http_transport))

        # set basic auth header
        if auth is not None:
            import base64
            auth_header = '{}:{}'.format(*auth)
            decoded = base64.b64encode(auth_header.encode()).decode('ascii')
            basic_auth = dict(Authorization='Basic {}'.format(decoded))
            self.http_transport.setCustomHeaders(basic_auth)

    def emit(self, batch):
        """Submits batches to Thrift HTTP Server through Binary Protocol.

        :type batch:
            :class:`~opencensus.ext.jaeger.trace_exporter.gen.jaeger.Batch`
        :param batch: Object to emit Jaeger spans.
        """
        try:
            self.client.submitBatches([batch])
            # it will call http_transport.flush() and
            # status code and message will be updated
            code = self.http_transport.code
            msg = self.http_transport.message
            if code >= 300 or code < 200:
                logging.error("Traces cannot be uploaded;\
                        HTTP status code: {}, message {}".format(code, msg))
        except Exception as e:  # pragma: NO COVER
            logging.error(getattr(e, 'message', e))

        finally:
            if self.http_transport.isOpen():
                self.http_transport.close()

    def export(self, batch):
        """
        :type batch: :class:
            `~opencensus.ext.jaeger.trace_exporter.gen.jaeger.Batch`
        :param batch: Object to export Jaeger spans.
        """
        self.transport.export(batch)


class AgentClientUDP(base_exporter.Exporter):
    """Implement a UDP client to agent.

    :type host_name: str
    :param host_name: (Optional) The host name of the Jaeger server.

    :type port: int
    :param port: (Optional) The port of the Jaeger server.

    :type max_packet_size: int
    :param max_packet_size: (Optional) Maximum size of UDP packet.

    :type client: :class:`type`
    :param client: Class for creating new client objects for agencies. It
                   should extend from the agent :class: `.AgentIface` type
                   and implement :meth:`.AgentIface.emitBatch`.Default and
                   only option to :class:`.AgentClient`.

    :type transport: :class:`type`
    :param transport: Class for creating new transport objects. It should
                      extend from the base_exporter :class:`.Transport` type
                      and implement :meth:`.Transport.export`. Defaults to
                      :class:`.SyncTransport`. The other option is
                      :class:`.AsyncTransport`.
    """

    def __init__(
            self,
            host_name=DEFAULT_HOST_NAME,
            port=DEFAULT_AGENT_PORT,
            max_packet_size=UDP_PACKET_MAX_LENGTH,
            client=agent.Client,
            transport=sync.SyncTransport):
        self.transport = transport(self)
        self.address = (host_name, port)
        self.max_packet_size = max_packet_size
        self.buffer = TTransport.TMemoryBuffer()
        self.client = client(
            iprot=TCompactProtocol.TCompactProtocol(trans=self.buffer))

    def emit(self, batch):
        """
        :type batch:
            :class:`~opencensus.ext.jaeger.trace_exporter.gen.jaeger.Batch`
        :param batch: Object to emit Jaeger spans.
        """
        udp_socket = None
        try:
            self.client._seqid = 0
            #  truncate and reset the position of BytesIO object
            self.buffer._buffer.truncate(0)
            self.buffer._buffer.seek(0)
            self.client.emitBatch(batch)
            buff = self.buffer.getvalue()
            if len(buff) > self.max_packet_size:
                logging.warn('Data exceeds the max UDP packet size; size {},\
                        max {}'.format(len(buff), self.max_packet_size))
            else:
                udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                udp_socket.sendto(buff, self.address)

        except Exception as e:  # pragma: NO COVER
            logging.error(getattr(e, 'message', e))

        finally:
            if udp_socket is not None:
                udp_socket.close()

    def export(self, batch):
        """
        :type batch:
            :class:`~opencensus.ext.jaeger.trace_exporter.gen.jaeger.Batch`
        :param batch: Object to export Jaeger spans.
        """
        self.transport.export(batch)
