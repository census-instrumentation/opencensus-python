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

"""Export opencensus spans to trace proto agent"""

import datetime
import grpc
import os
import socket
from threading import Lock
from opencensus.trace.exporters import base
from opencensus.trace.exporters.gen.opencensusd.agent.common.v1 import (
    common_pb2
)
from opencensus.trace.exporters.gen.opencensusd.agent.trace.v1 import (
    trace_service_pb2,
    trace_service_pb2_grpc
)
from opencensus.trace.exporters.transports import sync
from opencensus.trace.exporters.span_proto_exporter import utils

# Default agent endpoint
DEFAULT_ENDPOINT = 'localhost:50051'

# OpenCensus Version
VERSION = '0.1.6'


class SpanProtoExporter(base.Exporter):
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
                start_timestamp=utils.proto_ts_from_datetime(
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

        pb_spans = [utils.translate_to_opencensusd(
            span_data) for span_data in span_datas]

        yield trace_service_pb2.ExportTraceServiceRequest(
            node=self.node if self.send_node_in_export else None,
            spans=pb_spans)

    # TODO: better support for receiving config updates
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
