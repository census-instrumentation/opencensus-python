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

import codecs
import grpc
import mock
import os
import socket
import unittest

from google.protobuf.timestamp_pb2 import Timestamp

from opencensus.trace import span_context as span_context_module
from opencensus.trace import span_data as span_data_module
from opencensus.trace.exporters.span_proto_exporter import span_proto_exporter
from opencensus.trace.exporters.gen.opencensusd.agent.trace.v1 import trace_service_pb2
from opencensus.trace.exporters.gen.opencensusd.trace.v1 import trace_config_pb2


SERVICE_NAME = 'my-service'


class TestSpanProtoExporter(unittest.TestCase):

    def test_constructor(self):
        exporter = span_proto_exporter.SpanProtoExporter(
            service_name=SERVICE_NAME)

        self.assertEqual(exporter.endpoint, 'localhost:50051')

    def test_constructor_with_endpoint(self):
        expected_endpoint = '0.0.0.0:50000'
        exporter = span_proto_exporter.SpanProtoExporter(
            service_name=SERVICE_NAME,
            endpoint=expected_endpoint)

        self.assertEqual(exporter.endpoint, expected_endpoint)

    def test_constructor_with_client(self):
        client = mock.Mock()
        exporter = span_proto_exporter.SpanProtoExporter(
            service_name=SERVICE_NAME,
            client=client,
            transport=MockTransport)

        self.assertEqual(exporter.client, client)

    def test_constructor_node_host(self):
        exporter = span_proto_exporter.SpanProtoExporter(
            service_name=SERVICE_NAME,
            host_name='my host')

        self.assertEqual(exporter.node.service_info.name, SERVICE_NAME)
        self.assertEqual(exporter.node.library_info.language, 8)
        self.assertIsNotNone(exporter.node.library_info.version)

        self.assertEqual(exporter.node.identifier.host_name, 'my host')
        self.assertEqual(exporter.node.identifier.pid, os.getpid())

        self.assertIsNotNone(exporter.node.identifier.start_timestamp)
        self.assertGreater(exporter.node.identifier.start_timestamp.seconds, 0)

    def test_constructor_node(self):
        exporter = span_proto_exporter.SpanProtoExporter(
            service_name=SERVICE_NAME)

        self.assertEqual(exporter.node.service_info.name, SERVICE_NAME)
        self.assertEqual(exporter.node.library_info.language, 8)
        self.assertIsNotNone(exporter.node.library_info.version)

        self.assertEqual(exporter.node.identifier.host_name,
                         socket.gethostname())
        self.assertEqual(exporter.node.identifier.pid, os.getpid())

        self.assertIsNotNone(exporter.node.identifier.start_timestamp)
        self.assertGreater(exporter.node.identifier.start_timestamp.seconds, 0)

    def test_export(self):
        exporter = span_proto_exporter.SpanProtoExporter(
            service_name=SERVICE_NAME,
            transport=MockTransport)
        exporter.export({})

        self.assertTrue(exporter.transport.export_called)

    def test_emit(self):
        client = mock.Mock()
        client.Export.return_value = [1]
        exporter = span_proto_exporter.SpanProtoExporter(
            service_name=SERVICE_NAME,
            client=client,
            transport=MockTransport)

        exporter.emit({})

        self.assertTrue(client.Export.called)

    def test_emit_throw(self):
        client = mock.Mock()
        client.Export.side_effect = grpc.RpcError()
        exporter = span_proto_exporter.SpanProtoExporter(
            service_name=SERVICE_NAME,
            client=client,
            transport=MockTransport)

        # does not throw
        exporter.emit({})

        self.assertTrue(client.Export.called)

    def export_iterate(self, *args, **kwargs):
        self.export_requests = list(args[0])
        return iter(self.export_requests)

    def test_span_generator(self):

        hex_encoder = codecs.getencoder('hex')
        span_datas = [
            span_data_module.SpanData(
                name="name0",
                context=span_context_module.SpanContext(
                    trace_id='0e0c63257de34c92bf9efcd03927272e'),
                span_id='0e0c63257de34c92',
                parent_span_id=None,
                attributes=None,
                start_time=None,
                end_time=None,
                child_span_count=None,
                stack_trace=None,
                time_events=None,
                links=None,
                status=None,
                same_process_as_parent_span=None,
                span_kind=0),
            span_data_module.SpanData(
                name="name1",
                context=span_context_module.SpanContext(
                    trace_id='1e0c63257de34c92bf9efcd03927272e'),
                span_id='1e0c63257de34c92',
                parent_span_id=None,
                attributes=None,
                start_time=None,
                end_time=None,
                child_span_count=None,
                stack_trace=None,
                time_events=None,
                links=None,
                status=None,
                same_process_as_parent_span=None,
                span_kind=0)
        ]

        exporter = span_proto_exporter.SpanProtoExporter(
            service_name=SERVICE_NAME,
            transport=MockTransport)
        export_requests = list(exporter.generate_span_requests(span_datas))

        self.assertEqual(len(export_requests), 1)
        self.assertEqual(export_requests[0].node, exporter.node)
        self.assertEqual(len(export_requests[0].spans), 2)

        self.assertEqual(export_requests[0].spans[0].name.value, 'name0')
        self.assertEqual(export_requests[0].spans[1].name.value, 'name1')
        self.assertEqual(hex_encoder(export_requests[0].spans[0].trace_id)[
                         0], b'0e0c63257de34c92bf9efcd03927272e')
        self.assertEqual(hex_encoder(export_requests[0].spans[0].span_id)[
                         0], b'0e0c63257de34c92')
        self.assertEqual(hex_encoder(export_requests[0].spans[1].trace_id)[
                         0], b'1e0c63257de34c92bf9efcd03927272e')
        self.assertEqual(hex_encoder(export_requests[0].spans[1].span_id)[
                         0], b'1e0c63257de34c92')

    def test_basic_span_emit(self):
        hex_encoder = codecs.getencoder('hex')
        client = mock.Mock()

        # we need to make exporter iterate over passed generator,
        # otherwise iteration will happen after Export returns
        # and it won't be possible to check if node is included.
        # passed export request will be stored in self.export_requests
        client.Export.side_effect = self.export_iterate

        span_data = span_data_module.SpanData(
            name="name",
            context=span_context_module.SpanContext(
                trace_id='6e0c63257de34c92bf9efcd03927272e'),
            span_id='6e0c63257de34c92',
            parent_span_id=None,
            start_time=None,
            end_time=None,
            attributes=None,
            child_span_count=None,
            stack_trace=None,
            time_events=None,
            links=None,
            status=None,
            same_process_as_parent_span=None,
            span_kind=0)

        exporter = span_proto_exporter.SpanProtoExporter(
            service_name=SERVICE_NAME,
            client=client,
            transport=MockTransport)

        exporter.emit([span_data])

        self.assertTrue(client.Export.called)

        actual_request = self.export_requests[0]
        self.assertEqual(actual_request.node, exporter.node)

        pb_span = actual_request.spans[0]

        self.assertEqual(pb_span.name.value, "name")
        self.assertEqual(hex_encoder(pb_span.trace_id)[
                         0], b'6e0c63257de34c92bf9efcd03927272e')
        self.assertEqual(hex_encoder(pb_span.span_id)[0], b'6e0c63257de34c92')

    def test_second_span_emit_without_node(self):
        client = mock.Mock()

        # we need to make exporter iterate over passed generator,
        # otherwise iteration will happen after Export returns
        # and it won't be possible to check if node is included
        # passed export request will be stored in self.export_requests
        client.Export.side_effect = self.export_iterate

        span_data0 = span_data_module.SpanData(
            name="name0",
            context=span_context_module.SpanContext(
                trace_id='0e0c63257de34c92bf9efcd03927272e'),
            span_id='0e0c63257de34c92',
            parent_span_id=None,
            start_time=None,
            end_time=None,
            attributes=None,
            child_span_count=None,
            stack_trace=None,
            time_events=None,
            links=None,
            status=None,
            same_process_as_parent_span=None,
            span_kind=0)

        span_data1 = span_data_module.SpanData(
            name="name1",
            context=span_context_module.SpanContext(
                trace_id='1e0c63257de34c92bf9efcd03927272e'),
            span_id='1e0c63257de34c92',
            parent_span_id=None,
            start_time=None,
            end_time=None,
            attributes=None,
            child_span_count=None,
            stack_trace=None,
            time_events=None,
            links=None,
            status=None,
            same_process_as_parent_span=None,
            span_kind=0)

        exporter = span_proto_exporter.SpanProtoExporter(
            service_name=SERVICE_NAME,
            client=client,
            transport=MockTransport)

        exporter.emit([span_data0])

        actual_request = self.export_requests[0]
        self.assertIsNotNone(actual_request.node)
        self.assertEqual(actual_request.node, exporter.node)

        exporter.emit([span_data1])

        self.assertEqual(len(client.Export.mock_calls), 2)
        actual_request = self.export_requests[0]
        self.assertEqual(actual_request.node,
                         trace_service_pb2.ExportTraceServiceRequest().node)

    def test_second_span_emit_after_exception_with_node(self):
        client = mock.Mock()

        span_data0 = span_data_module.SpanData(
            name="name0",
            context=span_context_module.SpanContext(
                trace_id='0e0c63257de34c92bf9efcd03927272e'),
            span_id='0e0c63257de34c92',
            parent_span_id=None,
            start_time=None,
            end_time=None,
            attributes=None,
            child_span_count=None,
            stack_trace=None,
            time_events=None,
            links=None,
            status=None,
            same_process_as_parent_span=None,
            span_kind=0)

        exporter = span_proto_exporter.SpanProtoExporter(
            service_name=SERVICE_NAME,
            client=client,
            transport=MockTransport)

        client.Export.side_effect = grpc.RpcError()
        exporter.emit([span_data0])

        # we need to make exporter iterate over passed generator,
        # otherwise iteration will happen after Export returns
        # and it won't be possible to check if node is included
        # passed export request will be stored in self.export_requests
        client.Export.side_effect = self.export_iterate

        exporter.emit([span_data0])

        self.assertEqual(len(client.Export.mock_calls), 2)
        actual_request = self.export_requests[0]
        self.assertEqual(actual_request.node, exporter.node)

    def test_config_generator(self):

        config = trace_config_pb2.TraceConfig(
            constant_sampler=trace_config_pb2.ConstantSampler(
                decision=True))
        exporter = span_proto_exporter.SpanProtoExporter(
            service_name=SERVICE_NAME,
            transport=MockTransport)

        config_requests = list(exporter.generate_config_request(config))

        self.assertEqual(len(config_requests), 1)
        self.assertEqual(config_requests[0].node, exporter.node)
        self.assertEqual(config_requests[0].config, config)

    def config_iterate(self, *args, **kwargs):
        self.config_requests = list(args[0])
        return iter(self.config_requests)

    def test_second_config_update_without_node(self):
        client = mock.Mock()

        # we need to make exporter iterate over passed generator,
        # otherwise iteration will happen after Config returns
        # and it won't be possible to check if node is included.
        # passed config request will be stored in self.config_requests
        client.Config.side_effect = self.config_iterate

        config0 = trace_config_pb2.TraceConfig(
            constant_sampler=trace_config_pb2.ConstantSampler(
                decision=True))

        config1 = trace_config_pb2.TraceConfig(
            constant_sampler=trace_config_pb2.ConstantSampler(
                decision=False))

        exporter = span_proto_exporter.SpanProtoExporter(
            service_name=SERVICE_NAME,
            client=client,
            transport=MockTransport)

        exporter.update_config(config0)

        actual_request = self.config_requests[0]
        self.assertIsNotNone(actual_request.node)
        self.assertEqual(actual_request.node, exporter.node)

        exporter.update_config(config1)

        self.assertEqual(len(client.Config.mock_calls), 2)
        actual_request = self.config_requests[0]
        self.assertEqual(actual_request.node,
                         trace_service_pb2.ConfigTraceServiceRequest().node)

    def test_second_config_update_after_exception_with_node(self):
        client = mock.Mock()

        config0 = trace_config_pb2.TraceConfig(
            constant_sampler=trace_config_pb2.ConstantSampler(
                decision=True))

        config1 = trace_config_pb2.TraceConfig(
            constant_sampler=trace_config_pb2.ConstantSampler(
                decision=False))

        exporter = span_proto_exporter.SpanProtoExporter(
            service_name=SERVICE_NAME,
            client=client,
            transport=MockTransport)

        client.Config.side_effect = grpc.RpcError()
        with self.assertRaises(grpc.RpcError):
            exporter.update_config(config0)

        # we need to make exporter iterate over passed generator,
        # otherwise iteration will happen after Config returns
        # and it won't be possible to check if node is included.
        # passed config request will be stored in self.config_requests
        client.Config.side_effect = self.config_iterate

        exporter.update_config(config1)

        self.assertEqual(len(client.Config.mock_calls), 2)
        actual_request = self.config_requests[0]
        self.assertEqual(actual_request.node, exporter.node)

    def test_update_config_return_value(self):
        client = mock.Mock()

        client_config = trace_config_pb2.TraceConfig(
            constant_sampler=trace_config_pb2.ConstantSampler(
                decision=True))

        agent_config = trace_config_pb2.TraceConfig(
            probability_sampler=trace_config_pb2.ProbabilitySampler(
                samplingProbability=0.1))

        exporter = span_proto_exporter.SpanProtoExporter(
            service_name=SERVICE_NAME,
            client=client,
            transport=MockTransport)

        client.Config.return_value = iter([agent_config])
        actual_response = exporter.update_config(client_config)

        self.assertEqual(actual_response, agent_config)


class MockTransport(object):
    def __init__(self, exporter=None):
        self.export_called = False
        self.exporter = exporter

    def export(self, trace):
        self.export_called = True
