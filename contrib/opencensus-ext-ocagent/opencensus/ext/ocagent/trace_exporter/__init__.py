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
"""Export opencensus spans to ocagent"""

from threading import Lock
import grpc

from opencensus.common.transports import sync
from opencensus.ext.ocagent import utils as ocagent_utils
from opencensus.ext.ocagent.trace_exporter import utils
from opencensus.proto.agent.trace.v1 import trace_service_pb2
from opencensus.proto.agent.trace.v1 import trace_service_pb2_grpc
from opencensus.trace import base_exporter

# Default agent endpoint
DEFAULT_ENDPOINT = 'localhost:55678'

# OCAgent exporter version
EXPORTER_VERSION = '0.0.1'


class TraceExporter(base_exporter.Exporter):
    """Export the spans by sending them to opencensus agent.

    :type service_name: str
    :param service_name: name of the service

    :type host_name: str
    :param host_name: name of the host (machine or host name)

    :type endpoint: str
    :param endpoint: opencensus agent endpoint.

    :type client: class:`~.trace_service_pb2_grpc.TraceServiceStub`
    :param client: TraceService client stub.

    :type transport: :class:`type`
    :param transport: Class for creating new transport objects. It should
                      extend from the base_exporter :class:`.Transport` type
                      and implement :meth:`.Transport.export`. Defaults to
                      :class:`.SyncTransport`. The other option is
                      :class:`.AsyncTransport`.
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

        self.service_name = service_name
        self.node = ocagent_utils.get_node(self.service_name, host_name)

    def emit(self, span_datas):
        """
        :type span_datas: list of :class:
            `~opencensus.trace.span_data.SpanData`
        :param list of opencensus.trace.span_data.SpanData span_datas:
            SpanData tuples to emit
        """

        try:

            # TODO: keep the stream alive.
            # The stream is terminated after iteration completes.
            # To keep it alive, we can enqueue proto spans here
            # and asyncronously read them and send to the agent.
            responses = self.client.Export(
                self.generate_span_requests(span_datas))

            # read response
            for _ in responses:
                pass

        except grpc.RpcError:
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
        :param span_datas: SpanData tuples to convert to protobuf spans
                           and send to opensensusd agent

        :rtype: list of
                `~gen.opencensus.agent.trace.v1.trace_service_pb2.ExportTraceServiceRequest`
        :returns: List of span export requests.
        """

        pb_spans = [
            utils.translate_to_trace_proto(span_data)
            for span_data in span_datas
        ]

        # TODO: send node once per channel
        yield trace_service_pb2.ExportTraceServiceRequest(
            node=self.node,
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
            # TODO: keep the stream alive.
            # The stream is terminated after iteration completes.
            # To keep it alive, we can enqueue proto configs here
            # and asyncronously read them and send to the agent.
            config_responses = self.client.Config(
                self.generate_config_request(config))

            agent_config = next(config_responses)
            return agent_config

    def generate_config_request(self, config):
        """ConfigTraceServiceRequest generator.

        :type config: `~opencensus.proto.trace.v1.TraceConfig`
        :param config: Trace config with sampling and other settings

        :rtype: iterator of
               `~opencensus.proto.agent.trace.v1.CurrentLibraryConfig`
        :returns: Iterator of config requests.
        """

        # TODO: send node once per channel
        request = trace_service_pb2.CurrentLibraryConfig(
            node=self.node,
            config=config)

        yield request
