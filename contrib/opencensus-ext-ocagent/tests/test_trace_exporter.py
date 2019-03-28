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

from opencensus.common.version import __version__
from opencensus.ext.ocagent.trace_exporter.gen.opencensus.trace.v1 \
    import trace_config_pb2
from opencensus.ext.ocagent.trace_exporter import TraceExporter
from opencensus.trace import span_context as span_context_module
from opencensus.trace import span_data as span_data_module


SERVICE_NAME = 'my-service'


class TestTraceExporter(unittest.TestCase):

    def test_constructor(self):
        exporter = TraceExporter(
            service_name=SERVICE_NAME)

        self.assertEqual(exporter.endpoint, 'localhost:55678')

    def test_constructor_with_endpoint(self):
        expected_endpoint = '0.0.0.0:50000'
        exporter = TraceExporter(
            service_name=SERVICE_NAME,
            endpoint=expected_endpoint)

        self.assertEqual(exporter.endpoint, expected_endpoint)

    def test_constructor_with_client(self):
        client = mock.Mock()
        exporter = TraceExporter(
            service_name=SERVICE_NAME,
            client=client,
            transport=MockTransport)

        self.assertEqual(exporter.client, client)

    def test_constructor_node_host(self):
        exporter = TraceExporter(
            service_name=SERVICE_NAME,
            host_name='my host')

        self.assertEqual(exporter.node.service_info.name, SERVICE_NAME)
        self.assertEqual(exporter.node.library_info.language, 8)
        self.assertIsNotNone(exporter.node.library_info.exporter_version)
        self.assertIsNotNone(exporter.node.library_info.core_library_version)

        self.assertEqual(exporter.node.identifier.host_name, 'my host')
        self.assertEqual(exporter.node.identifier.pid, os.getpid())

        self.assertIsNotNone(exporter.node.identifier.start_timestamp)
        self.assertGreater(exporter.node.identifier.start_timestamp.seconds, 0)

    def test_constructor_node(self):
        exporter = TraceExporter(
            service_name=SERVICE_NAME)

        self.assertEqual(exporter.node.service_info.name, SERVICE_NAME)
        self.assertEqual(exporter.node.library_info.language, 8)
        self.assertIsNotNone(exporter.node.library_info.exporter_version)
        self.assertEqual(exporter.node.library_info.core_library_version,
                         __version__)

        self.assertEqual(exporter.node.identifier.host_name,
                         socket.gethostname())
        self.assertEqual(exporter.node.identifier.pid, os.getpid())

        self.assertIsNotNone(exporter.node.identifier.start_timestamp)
        self.assertGreater(exporter.node.identifier.start_timestamp.seconds, 0)

    def test_export(self):
        exporter = TraceExporter(
            service_name=SERVICE_NAME,
            transport=MockTransport)
        exporter.export({})

        self.assertTrue(exporter.transport.export_called)

    def test_emit(self):
        client = mock.Mock()
        client.Export.return_value = iter([1])
        exporter = TraceExporter(
            service_name=SERVICE_NAME,
            client=client,
            transport=MockTransport)

        exporter.emit({})

        self.assertTrue(client.Export.called)

    def test_emit_throw(self):
        client = mock.Mock()
        client.Export.side_effect = grpc.RpcError()
        exporter = TraceExporter(
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

        exporter = TraceExporter(
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

    def test_basic_spans_emit(self):
        hex_encoder = codecs.getencoder('hex')
        client = mock.Mock()
        client.Export.return_value = iter([1])

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

        exporter = TraceExporter(
            service_name=SERVICE_NAME,
            client=client,
            transport=MockTransport)

        exporter.emit([span_data0])

        actual_request0 = list(client.Export.call_args[0][0])[0]
        self.assertEqual(actual_request0.node, exporter.node)

        pb_span0 = actual_request0.spans[0]
        self.assertEqual(pb_span0.name.value, "name0")
        self.assertEqual(hex_encoder(pb_span0.trace_id)[
                         0], b'0e0c63257de34c92bf9efcd03927272e')
        self.assertEqual(hex_encoder(pb_span0.span_id)[0], b'0e0c63257de34c92')

        exporter.emit([span_data1])

        self.assertEqual(len(client.Export.mock_calls), 2)
        actual_request1 = list(client.Export.call_args[0][0])[0]
        self.assertEqual(actual_request1.node, exporter.node)
        pb_span1 = actual_request1.spans[0]
        self.assertEqual(pb_span1.name.value, "name1")
        self.assertEqual(hex_encoder(pb_span1.trace_id)[
                         0], b'1e0c63257de34c92bf9efcd03927272e')
        self.assertEqual(hex_encoder(pb_span1.span_id)[0], b'1e0c63257de34c92')

    def test_span_emit_exception(self):
        client = mock.Mock()

        span_data = span_data_module.SpanData(
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

        exporter = TraceExporter(
            service_name=SERVICE_NAME,
            client=client,
            transport=MockTransport)

        client.Export.side_effect = grpc.RpcError()

        # does not throw:
        exporter.emit([span_data])

        client.Export.return_value = iter([1])

        exporter.emit([span_data])

        self.assertEqual(len(client.Export.mock_calls), 2)
        actual_request = list(client.Export.call_args[0][0])[0]
        self.assertEqual(actual_request.node, exporter.node)

    def test_config_generator(self):

        config = trace_config_pb2.TraceConfig(
            constant_sampler=trace_config_pb2.ConstantSampler(
                decision=True))
        exporter = TraceExporter(
            service_name=SERVICE_NAME,
            transport=MockTransport)

        config_requests = list(exporter.generate_config_request(
            config))

        self.assertEqual(len(config_requests), 1)
        self.assertEqual(config_requests[0].node, exporter.node)
        self.assertEqual(config_requests[0].config, config)

    def test_config_update_exception(self):
        client = mock.Mock()

        config = trace_config_pb2.TraceConfig(
            constant_sampler=trace_config_pb2.ConstantSampler(
                decision=True))

        exporter = TraceExporter(
            service_name=SERVICE_NAME,
            client=client,
            transport=MockTransport)

        client.Config.side_effect = grpc.RpcError()
        with self.assertRaises(grpc.RpcError):
            exporter.update_config(config)

        client.Config.side_effect = lambda config: iter([config])

        exporter.update_config(config)

        self.assertEqual(len(client.Config.mock_calls), 2)
        actual_request = list(client.Config.call_args[0][0])[0]
        self.assertEqual(actual_request.node, exporter.node)

    def test_update_config_return_value(self):
        client = mock.Mock()

        client_config = trace_config_pb2.TraceConfig(
            constant_sampler=trace_config_pb2.ConstantSampler(
                decision=True))

        agent_config = trace_config_pb2.TraceConfig(
            probability_sampler=trace_config_pb2.ProbabilitySampler(
                samplingProbability=0.1))

        exporter = TraceExporter(
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
