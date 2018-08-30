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

"""Export the trace spans to OpenCensusD"""

import datetime
import grpc
import os
import socket
from threading import Lock
from google.protobuf.internal.well_known_types import ParseError
from google.protobuf.timestamp_pb2 import Timestamp
from google.protobuf.wrappers_pb2 import BoolValue, UInt32Value

from opencensus.trace.exporters import base
from opencensus.trace.exporters.transports import sync
from opencensus.trace.exporters.gen.opencensusd.trace.v1 import trace_pb2
from opencensus.trace.exporters.gen.opencensusd.agent.common.v1 import (
    common_pb2
)
from opencensus.trace.exporters.gen.opencensusd.agent.trace.v1 import (
    trace_service_pb2,
    trace_service_pb2_grpc
)

# Default agent endpoint
DEFAULT_ENDPOINT = 'localhost:50051'

# OpenCensus Version
VERSION = '0.1.6'


class OpenCensusDExporter(base.Exporter):
    """Export the spans by sending them to opencensus agent.

    :type service_name: str
    :param service_name: name of the service

    :type host_name: str
    :param host_name: name of the host (machine or host name)

    :type endpoint: str
    :param endpoint: opencensus agent endpoint.

    :type client: class:`~.trace_service_pb2_grpc.TraceServiceStub`
    :param client: OpenCensusD client.

    :type transport: :class:`type`
    :param transport: Class for creating new transport objects. It should
                      extend from the base :class:`.Transport` type and
                      implement :meth:`.Transport.export`. Defaults to
                      :class:`.SyncTransport`. The other option is
                      :class:`.BackgroundThreadTransport`.
    """

    def __init__(
            self,
            service_name,
            host_name=None,
            endpoint=None,
            client=None,
            transport=sync.SyncTransport):
        self.transport = transport(self)

        self.endpoint = DEFAULT_ENDPOINT if endpoint is None else endpoint

        if client is None:
            self.channel = grpc.insecure_channel(self.endpoint)
            self.client = trace_service_pb2_grpc.TraceServiceStub(
                channel=self.channel)
        else:
            self.client = client

        self.node = common_pb2.Node(
            identifier=common_pb2.ProcessIdentifier(
                host_name=socket.gethostname() if host_name is None
                else host_name,
                pid=os.getpid(),
                start_timestamp=self.proto_ts_from_datetime(
                    datetime.datetime.now())
            ),
            library_info=common_pb2.LibraryInfo(
                language=common_pb2.LibraryInfo.Language.Value('PYTHON'),
                version=VERSION
            ),
            service_info=common_pb2.ServiceInfo(name=service_name))

        self.send_node_in_config = True
        self.send_node_in_export = True

    def emit(self, span_datas):
        """
        :type span_datas: list of :class:
            `~opencensus.trace.span_data.SpanData`
        :param list of opencensus.trace.span_data.SpanData span_datas:
            SpanData tuples to emit
        """

        try:
            responses = self.client.Export(
                self.generate_span_requests(span_datas))

            # read response
            for _ in responses:
                pass

            # Node was successfully sent, unless there is a connectivity
            # issue between app and agent, Node should not be sent again
            self.send_node_in_export = False
        except grpc.RpcError:
            self.send_node_in_export = True
            self.send_node_in_config = True
            pass

    def export(self, span_datas):
        """Export the trace.
        Send trace to transport, and transport will call exporter.emit()
        to actually send the trace to the specified tracing
        backend.

        :type span_datas: list of :class:
            `~opencensus.trace.span_data.SpanData`
        :param list of opencensus.trace.span_data.SpanData span_datas:
            SpanData tuples to export
        """
        self.transport.export(span_datas)

    def generate_span_requests(self, span_datas):
        """Span request generator.

        :type span_datas: list of
                         :class:`~opencensus.trace.span_data.SpanData`
        :param span_datas: SpanData tuples to convert to protocuf spans
                           and send to opensensusd agent

        :rtype: list of
                `~gen.opencensusd.agent.trace.v1.trace_service_pb2.ExportTraceServiceRequest`
        :returns: List of span export requests.
        """

        pb_spans = [self.translate_to_opencensusd(
            span_data) for span_data in span_datas]

        yield trace_service_pb2.ExportTraceServiceRequest(
            node=self.node if self.send_node_in_export else None,
            spans=pb_spans)

    def update_config(self, config):
        """Sends TraceConfig to the agent and gets agent's config in reply.

        :type config: `~opencensus.proto.trace.v1.TraceConfig`
        :param config: Trace config with sampling and other settings

        :rtype: `~opencensus.proto.trace.v1.TraceConfig`
        :returns: Trace config from agent.
        """

        # do not allow updating config simultaneously
        lock = Lock()
        with lock:
            try:
                config_responses = self.client.Config(
                    self.generate_config_request(config))

                agent_config = next(config_responses)
                self.send_node_in_config = False
                return agent_config
            except grpc.RpcError as e:
                self.send_node_in_config = True
                self.send_node_in_export = True
                raise e

    def generate_config_request(self, config):
        """ConfigTraceServiceRequest generator.

        :type config: `~opencensus.proto.trace.v1.TraceConfig`
        :param config: Trace config with sampling and other settings

        :rtype: list of
               `~opencensus.proto.agent.trace.v1.ConfigTraceServiceRequest`
        :returns: List of config requests.
        """

        request = trace_service_pb2.ConfigTraceServiceRequest(
            node=self.node if self.send_node_in_config else None,
            config=config)

        yield request

    def translate_to_opencensusd(self, span_data):
        """Translates the opencensus spans to OpenCensusD spans.

        :type span_data: :class:`~opencensus.trace.span_data.SpanData`
        :param span_data: SpanData tuples to convert to protobuf spans

        :rtype: :class:`~opencensus.proto.trace.Span`
        :returns: Protobuf format span.
        """

        if not span_data:
            return None

        pb_span = trace_pb2.Span(
            name=trace_pb2.TruncatableString(value=span_data.name),
            kind=span_data.span_kind,
            trace_id=self.hex_str_to_bytes_str(span_data.context.trace_id),
            span_id=self.hex_str_to_bytes_str(span_data.span_id),
            parent_span_id=self.hex_str_to_bytes_str(span_data.parent_span_id)
            if span_data.parent_span_id is not None else None,
            start_time=self.proto_ts_from_datetime_str(span_data.start_time),
            end_time=self.proto_ts_from_datetime_str(span_data.end_time),
            status=trace_pb2.Status(
                code=span_data.status.code,
                message=span_data.status.message)
            if span_data.status is not None else None,
            same_process_as_parent_span=BoolValue(
                value=span_data.same_process_as_parent_span)
            if span_data.same_process_as_parent_span is not None
            else None,
            child_span_count=UInt32Value(value=span_data.child_span_count)
            if span_data.child_span_count is not None else None)

        # attributes
        if span_data.attributes is not None:
            for attribute_key, attribute_value \
                    in span_data.attributes.items():
                self.add_proto_attribute_value(
                    pb_span.attributes,
                    attribute_key,
                    attribute_value)

        # time events
        if span_data.time_events is not None:
            for span_data_event in span_data.time_events:
                if span_data_event.message_event is not None:
                    pb_event = pb_span.time_events.time_event.add()
                    pb_event.time.FromJsonString(span_data_event.timestamp)
                    self.set_proto_message_event(
                        pb_event.message_event,
                        span_data_event.message_event)
                elif span_data_event.annotation is not None:
                    pb_event = pb_span.time_events.time_event.add()
                    pb_event.time.FromJsonString(span_data_event.timestamp)
                    self.set_proto_annotation(
                        pb_event.annotation,
                        span_data_event.annotation)

        # links
        if span_data.links is not None:
            for link in span_data.links:
                pb_link = pb_span.links.link.add(
                    trace_id=self.hex_str_to_bytes_str(link.trace_id),
                    span_id=self.hex_str_to_bytes_str(link.span_id),
                    type=link.type)

                if link.attributes is not None and \
                        link.attributes.attributes is not None:
                    for attribute_key, attribute_value \
                            in link.attributes.attributes.items():
                        self.add_proto_attribute_value(
                            pb_link.attributes,
                            attribute_key,
                            attribute_value)

        # tracestate
        if span_data.context.tracestate is not None:
            for (key, value) in span_data.context.tracestate.items():
                pb_span.tracestate.entries.add(key=key, value=value)

        return pb_span

    def set_proto_message_event(
            self,
            pb_message_event,
            span_data_message_event):
        """Sets properties on the protobuf message event.

        :type pb_message_event:
            :class: `~opencensus.proto.trace.Span.TimeEvent.MessageEvent`
        :param pb_message_event: protobuf message event

        :type span_data_message_event:
            :class: `~opencensus.trace.time_event.MessageEvent`
        :param span_data_message_event: opencensus message event
        """

        pb_message_event.type = span_data_message_event.type
        pb_message_event.id = span_data_message_event.id
        pb_message_event.uncompressed_size = \
            span_data_message_event.uncompressed_size_bytes
        pb_message_event.compressed_size = \
            span_data_message_event.compressed_size_bytes

    def set_proto_annotation(self, pb_annotation, span_data_annotation):
        """Sets properties on the protobuf Span annotation.

        :type pb_annotation:
            :class: `~opencensus.proto.trace.Span.TimeEvent.Annotation`
        :param pb_annotation: protobuf annotation

        :type span_data_annotation:
            :class: `~opencensus.trace.time_event.Annotation`
        :param span_data_annotation: opencensus annotation

        """

        pb_annotation.description.value = span_data_annotation.description
        if span_data_annotation.attributes is not None \
                and span_data_annotation.attributes.attributes is not None:
            for attribute_key, attribute_value in \
                    span_data_annotation.attributes.attributes.items():
                self.add_proto_attribute_value(
                    pb_annotation.attributes,
                    attribute_key,
                    attribute_value)

    def hex_str_to_bytes_str(self, hex_str):
        """Converts the hex string to bytes string.

        :type hex_str: str
        :param hex_str: The hex tring representing trace_id or span_id.

        :rtype: str
        :returns: string representing byte array
        """

        return bytes(bytearray.fromhex(hex_str))

    def proto_ts_from_datetime_str(self, dt):
        """Converts string datetime in ISO format to protobuf timestamp.

        :type dt: str
        :param dt: string with datetime in ISO format

        :rtype: :class:`~google.protobuf.timestamp_pb2.Timestamp`
        :returns: protobuf timestamp
        """

        ts = Timestamp()
        if (dt is not None):
            try:
                ts.FromJsonString(dt)
            except ParseError:
                pass
        return ts

    def proto_ts_from_datetime(self, dt):
        """Converts datetime to protobuf timestamp.

        :type dt: datetime
        :param dt: date and time

        :rtype: :class:`~google.protobuf.timestamp_pb2.Timestamp`
        :returns: protobuf timestamp
        """

        ts = Timestamp()
        if (dt is not None):
            ts.FromDatetime(dt)
        return ts

    def add_proto_attribute_value(
            self,
            pb_attributes,
            attribute_key,
            attribute_value):
        """Sets string, int or boolean value on protobuf
            span, link or annotation attributes.

        :type pb_attributes:
            :class: `~opencensus.proto.trace.Span.Attributes`
        :param pb_attributes: protobuf Span's attributes property

        :type attribute_key: str
        :param attribute_key: attribute key to set

        :type attribute_value: str or int or bool
        :param attribute_value: attribute value
        """

        if isinstance(attribute_value, bool):
            pb_attributes.attribute_map[attribute_key].\
                bool_value = attribute_value
        elif isinstance(attribute_value, int):
            pb_attributes.attribute_map[attribute_key].\
                int_value = attribute_value
        elif isinstance(attribute_value, str):
            pb_attributes.attribute_map[attribute_key].\
                string_value.value = attribute_value
        else:
            pb_attributes.attribute_map[attribute_key].\
                string_value.value = str(attribute_value)
