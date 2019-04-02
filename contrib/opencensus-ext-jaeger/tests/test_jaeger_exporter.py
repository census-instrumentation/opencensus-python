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

import unittest

import mock

from opencensus.ext.jaeger import trace_exporter
from opencensus.ext.jaeger.trace_exporter.gen.jaeger import jaeger
from opencensus.trace import (attributes, link, span_context, span_data,
                              status, time_event)


class TestJaegerExporter(unittest.TestCase):
    def test_constructor_default(self):
        service_name = 'my_service'
        host_name = 'localhost'
        thrift_port = None
        agent_port = 6831
        agent_address = ('localhost', 6831)
        max_packet_size = 65000
        exporter = trace_exporter.JaegerExporter()
        agent_client = exporter.agent_client

        self.assertEqual(exporter.service_name, service_name)
        self.assertEqual(exporter.host_name, None)
        self.assertEqual(exporter.agent_host_name, host_name)
        self.assertEqual(exporter.agent_port, agent_port)
        self.assertEqual(exporter.port, thrift_port)
        self.assertEqual(exporter.endpoint, '')
        self.assertEqual(exporter.username, None)
        self.assertEqual(exporter.password, None)
        self.assertTrue(exporter.collector is None)
        self.assertTupleEqual(agent_client.address, agent_address)
        self.assertEqual(agent_client.max_packet_size, max_packet_size)
        # property should not construct new object
        client = exporter.agent_client
        self.assertEqual(agent_client, client)

    def test_constructor_explicit(self):
        service = 'opencensus-jaeger'
        host_name = 'example1.org'
        agent_host_name = 'example2.org'
        username = 'username'
        password = 'password'
        port = 14268
        host_name = 'localhost'
        thrift_url = 'http://localhost:14268/api/traces?format=jaeger.thrift'
        auth = (username, password)

        exporter = trace_exporter.JaegerExporter(
            service_name=service,
            host_name=host_name,
            agent_host_name=agent_host_name,
            username=username,
            password=password,
            port=port)
        self.assertEqual(exporter.service_name, service)
        self.assertEqual(exporter.agent_host_name, agent_host_name)
        self.assertEqual(exporter.host_name, host_name)
        self.assertFalse(exporter.collector is None)
        self.assertEqual(exporter.collector.thrift_url, thrift_url)
        self.assertEqual(exporter.collector.auth, auth)
        # property should not construct new object
        collector = exporter.collector
        self.assertEqual(exporter.collector, collector)
        # property should construct new object
        exporter._collector = None
        exporter.username = None
        exporter.password = None
        self.assertNotEqual(exporter.collector, collector)
        self.assertTrue(exporter.collector.auth is None)

    def test_export(self):
        exporter = trace_exporter.JaegerExporter(
            service_name='my_service', transport=MockTransport)
        exporter.export({})

        collector = trace_exporter.Collector(
            transport=MockTransport, http_transport=MockTransport)
        collector.export({})

        agent = trace_exporter.AgentClientUDP(transport=MockTransport)
        agent.export({})

        self.assertTrue(exporter.transport.export_called)
        self.assertTrue(collector.transport.export_called)
        self.assertTrue(agent.transport.export_called)

    @mock.patch('opencensus.ext.jaeger.trace_exporter.logging')
    def test_agent_emit_succeeded(self, mock_logging):
        agent_client = trace_exporter.AgentClientUDP(client=MockClient)

        agent_client.emit({})
        self.assertTrue(agent_client.client.emit_called)
        self.assertFalse(mock_logging.warn.called)

    @mock.patch('opencensus.ext.jaeger.trace_exporter.logging')
    def test_packet_capacity_exceeded(self, mock_logging):
        agent_client = trace_exporter.AgentClientUDP(
            client=MockClient, max_packet_size=-1)
        agent_client.emit({})
        self.assertTrue(mock_logging.warn.called)

    @mock.patch('opencensus.ext.jaeger.trace_exporter.logging')
    def test_collector_emit_failed(self, mock_logging):
        url = 'http://localhost:14268/api/traces?format=jaeger.thrift'
        collector = trace_exporter.Collector(
            thrift_url=url, http_transport=MockTransport, client=MockClient)
        collector.http_transport.is_open = False
        collector.http_transport.code = 400
        collector.http_transport.message = 'failure'
        collector.emit(MockBatch())
        self.assertTrue(mock_logging.error.called)
        self.assertFalse(collector.http_transport.is_closed)

    @mock.patch('opencensus.ext.jaeger.trace_exporter.logging')
    def test_collector_emit_succeeded(self, mock_logging):
        url = 'http://localhost:14268/api/traces?format=jaeger.thrift'
        collector = trace_exporter.Collector(
            thrift_url=url, http_transport=MockTransport, client=MockClient)
        collector.http_transport.is_open = True
        collector.http_transport.code = 200
        collector.http_transport.message = 'success'
        collector.emit(MockBatch())
        self.assertFalse(mock_logging.error.called)
        self.assertTrue(collector.http_transport.is_closed)

    def test_collector_auth_headers(self):
        collector = trace_exporter.Collector(
            http_transport=MockTransport, auth=('user', 'pass'))
        self.assertTrue(collector.http_transport.headers_set)

        collector = trace_exporter.Collector(http_transport=MockTransport)
        self.assertFalse(collector.http_transport.headers_set)

    @mock.patch.object(
        trace_exporter.JaegerExporter,
        'agent_client',
        new_callable=mock.PropertyMock)
    @mock.patch.object(
        trace_exporter.JaegerExporter,
        'collector',
        new_callable=mock.PropertyMock)
    @mock.patch.object(trace_exporter.JaegerExporter, 'translate_to_jaeger')
    def test_emit_succeeded(self, translate_mock, collector_mock, agent_mock):
        collector = collector_mock.return_value = MockTransport()
        agent = agent_mock.return_value = MockTransport()
        exporter = trace_exporter.JaegerExporter()
        translate_mock.return_value = {'test': 'mock'}
        exporter.emit([])
        self.assertTrue(agent.export_called)
        self.assertTrue(collector.export_called)

        collector_mock.return_value = None
        agent = agent_mock.return_value = MockTransport()
        exporter = trace_exporter.JaegerExporter()
        exporter.emit([])
        self.assertTrue(agent.export_called)

    def test_translate_to_jaeger(self):
        self.maxDiff = None
        trace_id_high = '6e0c63257de34c92'
        trace_id_low = 'bf9efcd03927272e'
        trace_id = trace_id_high + trace_id_low
        span_id = '6e0c63257de34c92'
        parent_span_id = '1111111111111111'

        span_attributes = {
            'key_bool': False,
            'key_string': 'hello_world',
            'key_int': 3,
            'key_double': 111.22,
            'key_unsupported_type': ()
        }

        annotation_attributes = {
            'annotation_bool': True,
            'annotation_string': 'annotation_test',
            'key_float': .3,
            'key_unsupported_type': {}
        }

        link_attributes = {'key_bool': True}

        import datetime
        s = '2017-08-15T18:02:26.071158'
        time = datetime.datetime.strptime(s, '%Y-%m-%dT%H:%M:%S.%f')
        time_events = [
            time_event.TimeEvent(
                timestamp=time,
                annotation=time_event.Annotation(
                    description='First Annotation',
                    attributes=attributes.Attributes(annotation_attributes))),
            time_event.TimeEvent(
                timestamp=time,
                message_event=time_event.MessageEvent(
                    id='message-event-id',
                    uncompressed_size_bytes=0,
                )),
        ]

        time_events2 = [
            time_event.TimeEvent(
                timestamp=time,
                annotation=time_event.Annotation(
                    description='First Annotation',
                    attributes=None)),
            time_event.TimeEvent(
                timestamp=time,
                message_event=time_event.MessageEvent(
                    id='message-event-id',
                    uncompressed_size_bytes=0,
                )),
        ]

        links = [
            link.Link(
                trace_id=trace_id,
                span_id=span_id,
                type=link.Type.CHILD_LINKED_SPAN,
                attributes=link_attributes),
            link.Link(
                trace_id=trace_id,
                span_id=span_id,
                type=link.Type.PARENT_LINKED_SPAN,
                attributes=link_attributes),
            link.Link(
                trace_id=trace_id,
                span_id=span_id,
                type=link.Type.TYPE_UNSPECIFIED,
                attributes=link_attributes)
        ]

        span_status = status.Status(code=200, message='success')

        start_time = '2017-08-15T18:02:26.071158Z'
        end_time = '2017-08-15T18:02:36.071158Z'

        span_datas = [
            span_data.SpanData(
                name='test1',
                context=span_context.SpanContext(trace_id=trace_id),
                span_id=span_id,
                parent_span_id=parent_span_id,
                attributes=span_attributes,
                start_time=start_time,
                end_time=end_time,
                child_span_count=0,
                stack_trace=None,
                time_events=time_events,
                links=links,
                status=span_status,
                same_process_as_parent_span=None,
                span_kind=0,
            ),
            span_data.SpanData(
                name='test2',
                context=None,
                span_id=span_id,
                parent_span_id=None,
                attributes=None,
                start_time=start_time,
                end_time=end_time,
                child_span_count=None,
                stack_trace=None,
                time_events=time_events2,
                links=None,
                status=None,
                same_process_as_parent_span=None,
                span_kind=None,
            ),
            span_data.SpanData(
                name='test3',
                context=None,
                span_id=span_id,
                parent_span_id=None,
                attributes=None,
                start_time=start_time,
                end_time=end_time,
                child_span_count=None,
                stack_trace=None,
                time_events=None,
                links=None,
                status=None,
                same_process_as_parent_span=None,
                span_kind=None,
            )
        ]

        exporter = trace_exporter.JaegerExporter()

        spans = exporter.translate_to_jaeger(span_datas)
        expected_spans = [
            jaeger.Span(
                traceIdHigh=7929822056569588882,
                traceIdLow=-4638992594902767826,
                spanId=7929822056569588882,
                parentSpanId=1229782938247303441,
                operationName='test1',
                startTime=1502820146071158,
                duration=10000000,
                flags=0,
                tags=[
                    jaeger.Tag(
                        key='key_bool', vType=jaeger.TagType.BOOL,
                        vBool=False),
                    jaeger.Tag(
                        key='key_string',
                        vType=jaeger.TagType.STRING,
                        vStr='hello_world'),
                    jaeger.Tag(
                        key='key_int', vType=jaeger.TagType.LONG, vLong=3),
                    jaeger.Tag(
                        key='key_double',
                        vType=jaeger.TagType.DOUBLE,
                        vDouble=111.22),
                    jaeger.Tag(
                        key='status.code',
                        vType=jaeger.TagType.LONG,
                        vLong=200),
                    jaeger.Tag(
                        key='status.message',
                        vType=jaeger.TagType.STRING,
                        vStr='success')
                ],
                references=[
                    jaeger.SpanRef(
                        refType=jaeger.SpanRefType.CHILD_OF,
                        traceIdHigh=7929822056569588882,
                        traceIdLow=-4638992594902767826,
                        spanId=7929822056569588882),
                    jaeger.SpanRef(
                        refType=jaeger.SpanRefType.FOLLOWS_FROM,
                        traceIdHigh=7929822056569588882,
                        traceIdLow=-4638992594902767826,
                        spanId=7929822056569588882),
                    jaeger.SpanRef(
                        refType=None,
                        traceIdHigh=7929822056569588882,
                        traceIdLow=-4638992594902767826,
                        spanId=7929822056569588882)
                ],
                logs=[
                    jaeger.Log(
                        timestamp=1502820146071158,
                        fields=[
                            jaeger.Tag(
                                key='annotation_bool',
                                vType=jaeger.TagType.BOOL,
                                vBool=True),
                            jaeger.Tag(
                                key='annotation_string',
                                vType=jaeger.TagType.STRING,
                                vStr='annotation_test'),
                            jaeger.Tag(
                                key='key_float',
                                vType=jaeger.TagType.DOUBLE,
                                vDouble=0.3),
                            jaeger.Tag(
                                key='message',
                                vType=jaeger.TagType.STRING,
                                vStr='First Annotation')
                        ])
                ]),
            jaeger.Span(
                operationName="test2",
                traceIdHigh=7929822056569588882,
                traceIdLow=-4638992594902767826,
                spanId=7929822056569588882,
                parentSpanId=0,
                startTime=1502820146071158,
                duration=10000000,
                logs=[
                    jaeger.Log(
                        timestamp=1502820146071158,
                        fields=[
                            jaeger.Tag(
                                key='message',
                                vType=jaeger.TagType.STRING,
                                vStr='First Annotation')
                        ])
                ]
            ),
            jaeger.Span(
                operationName="test3",
                traceIdHigh=7929822056569588882,
                traceIdLow=-4638992594902767826,
                spanId=7929822056569588882,
                parentSpanId=0,
                startTime=1502820146071158,
                duration=10000000,
                logs=[]
            )
        ]

        spans_json = [span.format_span_json() for span in spans]
        expected_spans_json = [
            span.format_span_json() for span in expected_spans
        ]
        span = spans_json[0]
        expected_span = expected_spans_json[0]

        try:
            listsEqual = self.assertCountEqual
        except AttributeError:
            listsEqual = self.assertItemsEqual

        log = span.get('logs')[0]
        expected_log = expected_span.get('logs')[0]
        self.assertEqual(log.get('timestamp'), expected_log.get('timestamp'))
        listsEqual(log.get('fields'), expected_log.get('fields'))
        listsEqual(span.get('tags'), expected_span.get('tags'))
        listsEqual(span.get('references'), expected_span.get('references'))
        self.assertEqual(
            span.get('traceIdHigh'), expected_span.get('traceIdHigh'))
        self.assertEqual(
            span.get('traceIdLow'), expected_span.get('traceIdLow'))
        self.assertEqual(span.get('spanId'), expected_span.get('spanId'))
        self.assertEqual(
            span.get('parentSpanId'), expected_span.get('parentSpanId'))
        self.assertEqual(
            span.get('operationName'), expected_span.get('operationName'))
        self.assertEqual(span.get('startTime'), expected_span.get('startTime'))
        self.assertEqual(span.get('duration'), expected_span.get('duration'))
        self.assertEqual(span.get('flags'), expected_span.get('flags'))
        self.assertEqual(spans_json[1], expected_spans_json[1])

        self.assertEqual(spans_json[2], expected_spans_json[2])

    def test_convert_hex_str_to_int(self):
        invalid_id = '990c63257de34c92'
        trace_exporter._convert_hex_str_to_int(invalid_id)
        valid_id = '290c63257de34c92'
        trace_exporter._convert_hex_str_to_int(valid_id)
        self.assertIsNone(trace_exporter._convert_hex_str_to_int(None))


class MockBatch(object):
    def write(self, iprot):
        return None


class MockTransport(object):
    def __init__(self, exporter=None, uri_or_host=None):
        self.export_called = False
        self.headers_set = False
        self.exporter = exporter
        self.code = 200
        self.message = 'success'
        self.uri_or_host = uri_or_host
        self.scheme = 'http'
        self.is_open = True
        self.is_closed = False

    def export(self, trace):
        self.export_called = True

    def setCustomHeaders(self, headers):
        self.headers_set = True

    def close(self):
        self.is_closed = True

    def isOpen(self):
        return self.is_open


class MockClient(object):
    def __init__(self, iprot=None):
        self.emit_called = False
        self.iprot = iprot

    def emitBatch(self, batch):
        self.emit_called = True

    def submitBatches(self, batches):
        return None
