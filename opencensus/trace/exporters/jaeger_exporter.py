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
import calendar
import datetime

from thrift.transport import TTransport, THttpClient
from thrift.protocol import TCompactProtocol, TBinaryProtocol

from opencensus.trace import span_data, link
from opencensus.trace.exporters import base
from opencensus.trace.exporters.transports import sync
from opencensus.trace.exporters.gen.jaeger import jaeger
from opencensus.trace.exporters.gen.jaeger import agent

DEFAULT_HOST_NAME = 'localhost'
DEFAULT_AGENT_PORT = 6931
DEFAULT_ENDPOINT = '/api/traces'

ISO_DATETIME_REGEX = '%Y-%m-%dT%H:%M:%S.%fZ'
UDP_PACKET_MAX_LENGTH = 65000

logging = logging.getLogger(__name__)


class JaegerExporter(base.Exporter):
    """Exports the spans to Jaeger.

    :type service_name: str
    :param service_name: Service that logged an annotation in a trace.
                         Classifier when query for spans.

    :type host_name: str
    :param host_name: (Optional) The host name of the Jaeger HTTP Thrift.

    :type port: int
    :param port: (Optional) The port of the Jaeger HTTP Thrift.

    :type endpoint: str
    :param port: (Optional) The endpoint of the Jaeger HTTP Thrift .

    :type agent_host_name: str
    :param agent_host_name: (Optional) The host name of the Jaeger-Agent.

    :type agent_port: int
    :param agent_port: (Optional) The port of the Jaeger-Agent.

    :type username: str
    :param username: (Optional) The user name of the Basic Auth
                     if authentication is required.

    :type password: str
    :param password: (Optional) The password of the Basic Auth
                     if authentication is required.

    :type transport: :class:`type`
    :param transport: Class for creating new transport objects. It should
                      extend from the base :class:`.Transport` type and
                      implement :meth:`.Transport.export`. Defaults to
                      :class:`.SyncTransport`. The other option is
                      :class:`.BackgroundThreadTransport`.
    """

    def __init__(
            self,
            service_name='my_service',
            host_name=None,
            port=None,
            endpoint='',
            agent_host_name=DEFAULT_HOST_NAME,
            agent_port=DEFAULT_AGENT_PORT,
            agent_endpoint=DEFAULT_ENDPOINT,
            username='',
            password='',
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
        self.agent_client = self._agent_client
        self.collector = self._collector

    @property
    def _agent_client(self):
        return AgentClientUDP(
            host_name=self.agent_host_name,
            port=self.agent_port)

    @property
    def _collector(self):
        if self.host_name is None or self.port is None:
            return None

        thrift_url = 'http://{}:{}{}{}'.format(
            self.host_name,
            self.port,
            self.endpoint,
            DEFAULT_ENDPOINT)

        auth = None
        if self.username != '' and self.password != '':
            auth = (self.username, self.password)

        return Collector(thrift_url=thrift_url, auth=auth)

    def emit(self, span_datas):
        """
        :type span_datas: list of :class:
            `~opencensus.trace.span_data.SpanData`
        :param list of opencensus.trace.span_data.SpanData span_datas:
            SpanData tuples to emit
        """
        trace = span_data.format_legacy_trace_json(span_datas)

        jaeger_spans = self.translate_to_jaeger(trace)

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
        :param list of opencensus.trace.span_data.SpanData span_datas:
            SpanData tuples to export
        """
        self.transport.export(span_datas)

    def translate_to_jaeger(self, trace):
        """Translate the spans json to Jaeger format.

        :type trace: dict
        :param trace: Trace dictionary

        :rtype: list
        :returns: List of jaeger.Span objects generated by Thrift.
        """

        trace_id = trace.get('traceId', '')
        spans = trace.get('spans')
        jaeger_spans = []

        for span in spans:
            start_datetime = datetime.datetime.strptime(
                span.get('startTime'), ISO_DATETIME_REGEX)
            start_microsec = calendar.timegm(start_datetime.timetuple()) * 1000

            end_datetime = datetime.datetime.strptime(
                span.get('endTime'), ISO_DATETIME_REGEX)
            end_microsec = calendar.timegm(end_datetime.timetuple()) * 1000

            duration_microsec = end_microsec - start_microsec

            tags = _extract_tags(span)

            status = span.get('status', None)
            if status is not None:
                tags.append(jaeger.Tag(
                    key='status.code',
                    vType=jaeger.TagType.LONG,
                    vLong=status.get('code')))

                tags.append(jaeger.Tag(
                    key='status.message',
                    vType=jaeger.TagType.STRING,
                    vStr=status.get('message')))

            refs = _extract_refs_from_span(span)
            logs = _extract_logs_from_span(span)

            context = span.get('context')
            flags = None
            if context is not None and context.get('traceOptions') is not None:
                flags = int(context.get('traceOptions'))

            span_id = span.get('spanId', '')
            parent_span_id = span.get('parentSpanId', '')

            jaeger_span = jaeger.Span(
                traceIdHigh=_convert_hex_str_to_int(trace_id[0:8]),
                traceIdLow=_convert_hex_str_to_int(trace_id[8:16]),
                spanId=_convert_hex_str_to_int(span_id),
                operationName=span.get('name'),
                startTime=int(round(start_microsec)),
                duration=int(round(duration_microsec)),
                tags=tags,
                logs=logs,
                references=refs,
                flags=flags,
                parentSpanId=_convert_hex_str_to_int(parent_span_id))

            jaeger_spans.append(jaeger_span)

        return jaeger_spans


def _extract_refs_from_span(span):
    refs = []
    for link_el in span.get('links', {}).get('link', []):
        if not isinstance(link_el, dict):
            continue

        trace_id = link_el.get('trace_id', '')
        span_id = link_el.get('span_id', '')

        refs.append(jaeger.SpanRef(
            refType=_convert_reftype_to_jaeger_reftype(link_el.get('type')),
            traceIdHigh=_convert_hex_str_to_int(trace_id[0:8]),
            traceIdLow=_convert_hex_str_to_int(trace_id[8:16]),
            spanId=_convert_hex_str_to_int(span_id)))
    return refs


def _convert_reftype_to_jaeger_reftype(ref):
    """Convert opencensus reference types to jaeger reference types."""
    if ref == link.Type.CHILD_LINKED_SPAN:
        return jaeger.SpanRefType.CHILD_OF
    if ref == link.Type.PARENT_LINKED_SPAN:
        return jaeger.SpanRefType.FOLLOWS_FROM
    return None


def _convert_hex_str_to_int(val):
    return int(val, 16) if val else None


def _extract_logs_from_span(span):
    logs = []
    for time_event in span.get('timeEvents', {}).get('timeEvent', []):
        annotation = time_event.get('annotation')
        if not isinstance(annotation, dict):
            continue

        fields = _extract_tags(annotation)

        fields.append(jaeger.Tag(
            key='message',
            vType=jaeger.TagType.STRING,
            vStr=annotation.get('description')))

        event_time = datetime.datetime.strptime(
            time_event.get('time'), ISO_DATETIME_REGEX)
        timestamp = calendar.timegm(event_time.timetuple()) * 1000

        logs.append(jaeger.Log(timestamp=timestamp, fields=fields))
    return logs


def _extract_tags(attr):
    tags = []
    for attribute_key, attribute_value in attr.get('attributes', {}).get(
            'attributeMap', {}).items():
        if not isinstance(attribute_value, dict):
            continue
        tag = _convert_attribute_to_tag(attribute_key, attribute_value)
        if tag is not None:
            tags.append(tag)
    return tags


def _convert_attribute_to_tag(key, attr):
    """Convert the attributes to jaeger tags."""
    if attr.get('string_value') is not None:
        return jaeger.Tag(
            key=key,
            vStr=attr.get('string_value').get('value'),
            vType=jaeger.TagType.STRING)
    if attr.get('int_value') is not None:
        return jaeger.Tag(
            key=key,
            vLong=attr.get('int_value'),
            vType=jaeger.TagType.LONG)
    if attr.get('bool_value') is not None:
        return jaeger.Tag(
            key=key,
            vBool=attr.get('bool_value'),
            vType=jaeger.TagType.BOOL)
    logging.warn('Could not serialize attribute to tag {}'.format(attr))
    return None


class Collector(base.Exporter):
    """Submits collected spans to Thrift HTTP server.

    :type thrift_url: str
    :param thrift_url: URL of the Jaeger HTTP Thrift.

    :type auth: tupple
    :param auth: (Optional) Auth tupple that contains username and
                password for Basic Auth.

    :type transport: :class:`type`
    :param transport: Class for creating new transport objects. It should
                      extend from the base :class:`.Transport` type and
                      implement :meth:`.Transport.export`. Defaults to
                      :class:`.SyncTransport`. The other option is
                      :class:`.BackgroundThreadTransport`.

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

    def emit(self, batch):
        """Submits batches to Thrift HTTP Server through Binary Protocol.

        :type batch: :class: `~opencensus.trace.exporters.gen.jaeger.Batch`
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
            self.http_transport.close()

    def export(self, batch):
        """
        :type batch: :class: `~opencensus.trace.exporters.gen.jaeger.Batch`
        :param batch: Object to export Jaeger spans.
        """
        self.transport.export(batch)


class AgentClientUDP(base.Exporter):
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
                      extend from the base :class:`.Transport` type and
                      implement :meth:`.Transport.export`. Defaults to
                      :class:`.SyncTransport`. The other option is
                      :class:`.BackgroundThreadTransport`.
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
        self.buffer = self._memory_buffer
        self.client = client(
            iprot=TCompactProtocol.TCompactProtocol(trans=self.buffer))

    @property
    def _memory_buffer(self):
        return TTransport.TMemoryBuffer()

    def emit(self, batch):
        """
        :type batch: :class: `~opencensus.trace.exporters.gen.jaeger.Batch`
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
        :type batch: :class: `~opencensus.trace.exporters.gen.jaeger.Batch`
        :param batch: Object to export Jaeger spans.
        """
        self.transport.export(batch)
