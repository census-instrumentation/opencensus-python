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

from opencensus.trace import link as link_module
from opencensus.trace.exporters import jaeger_exporter
from opencensus.trace.exporters.gen.jaeger import jaeger


class TestJaegerExporter(unittest.TestCase):
    def test_constructor_default(self):
        service_name = 'my_service'
        host_name = 'localhost'
        thrift_port = None
        agent_port = 6931
        agent_address = ('localhost', 6931)
        max_packet_size = 65000
        exporter = jaeger_exporter.JaegerExporter()
        agent_client = exporter.agent_client

        self.assertEqual(exporter.service_name, service_name)
        self.assertEqual(exporter.host_name, None)
        self.assertEqual(exporter.agent_host_name, host_name)
        self.assertEqual(exporter.agent_port, agent_port)
        self.assertEqual(exporter.port, thrift_port)
        self.assertEqual(exporter.endpoint, '')
        self.assertEqual(exporter.username, '')
        self.assertEqual(exporter.password, '')
        self.assertTrue(exporter.collector is None)
        self.assertTupleEqual(agent_client.address, agent_address)
        self.assertEqual(agent_client.max_packet_size, max_packet_size)

    def test_constructor_explicit(self):
        service = 'opencensus-jaeger'
        host_name = 'example1.org'
        agent_host_name = 'example2.org'
        username = 'username'
        password = 'password'
        port = 14268
        host_name = 'localhost'
        thrift_url = 'http://localhost:14268/api/traces'
        auth = ('username', 'password')

        exporter = jaeger_exporter.JaegerExporter(
            service_name=service,
            host_name=host_name,
            agent_host_name=agent_host_name,
            username=username,
            password=password,
            port=port,
        )
        self.assertEqual(exporter.service_name, service)
        self.assertEqual(exporter.agent_host_name, agent_host_name)
        self.assertEqual(exporter.host_name, host_name)
        self.assertFalse(exporter.collector is None)
        self.assertFalse(exporter.collector.auth is None)
        self.assertEqual(exporter.collector.thrift_url, thrift_url)
        self.assertTupleEqual(exporter.collector.auth, auth)

        exporter.username = ''
        exporter.password = ''
        collector = exporter._collector
        self.assertTrue(collector.auth is None)

    def test_export(self):
        exporter = jaeger_exporter.JaegerExporter(
            service_name='my_service', transport=MockTransport)
        exporter.export({})

        collector = jaeger_exporter.Collector(
            transport=MockTransport, http_transport=MockTransport)
        collector.export({})

        agent = jaeger_exporter.AgentClientUDP(transport=MockTransport)
        agent.export({})

        self.assertTrue(exporter.transport.export_called)
        self.assertTrue(collector.transport.export_called)
        self.assertTrue(agent.transport.export_called)

    @mock.patch('opencensus.trace.exporters.jaeger_exporter.logging')
    def test_agent_emit_succeeded(self, mock_logging):
        agent_client = jaeger_exporter.AgentClientUDP(client=MockClient)

        agent_client.emit({})
        self.assertTrue(agent_client.client.emit_called)
        self.assertFalse(mock_logging.warn.called)

    @mock.patch('opencensus.trace.exporters.jaeger_exporter.logging')
    def test_packet_capacity_exceeded(self, mock_logging):
        agent_client = jaeger_exporter.AgentClientUDP(
            client=MockClient, max_packet_size=-1)
        agent_client.emit({})
        self.assertTrue(mock_logging.warn.called)

    @mock.patch('opencensus.trace.exporters.jaeger_exporter.logging')
    def test_collector_emit_failed(self, mock_logging):
        url = 'http://localhost:14268/api/traces?format=jaeger.thrift'
        http_transport = MockTransport()
        collector = jaeger_exporter.Collector(
            thrift_url=url, http_transport=MockTransport, client=MockClient)
        collector.http_transport.code = 400
        collector.http_transport.message = 'failure'
        collector.emit(MockBatch())
        self.assertTrue(mock_logging.error.called)

    @mock.patch('opencensus.trace.exporters.jaeger_exporter.logging')
    def test_collector_emit_succeeded(self, mock_logging):
        url = 'http://localhost:14268/api/traces?format=jaeger.thrift'
        collector = jaeger_exporter.Collector(
            thrift_url=url, http_transport=MockTransport, client=MockClient)
        collector.http_transport.code = 200
        collector.http_transport.message = 'success'
        collector.emit(MockBatch())
        self.assertFalse(mock_logging.error.called)

    @mock.patch.object(
        jaeger_exporter.JaegerExporter,
        '_agent_client',
        new_callable=mock.PropertyMock)
    @mock.patch.object(
        jaeger_exporter.JaegerExporter,
        '_collector',
        new_callable=mock.PropertyMock)
    @mock.patch.object(jaeger_exporter.JaegerExporter, 'translate_to_jaeger')
    def test_emit_succeeded(self, translate_mock, collector_mock, agent_mock):
        collector = collector_mock.return_value = MockTransport()
        agent = agent_mock.return_value = MockTransport()
        exporter = jaeger_exporter.JaegerExporter()
        translate_mock.return_value = {'test': 'mock'}
        exporter.emit([])
        self.assertTrue(agent.export_called)
        self.assertTrue(collector.export_called)

        collector_mock.return_value = None
        agent = agent_mock.return_value = MockTransport()
        exporter = jaeger_exporter.JaegerExporter()
        exporter.emit([])
        self.assertTrue(agent.export_called)

    def test_translate_to_jaeger(self):
        self.maxDiff = None
        trace_id = '6e0c63257de34c92bf9efcd03927272e'
        span_id = '6e0c63257de34c92'
        parent_span_id = '1111111111111111'

        attributes = {
            'attributeMap': {
                'key_bool': {
                    'bool_value': False
                },
                'key_string': {
                    'string_value': {
                        'truncated_byte_count': 0,
                        'value': 'hello_world'
                    }
                },
                'key_int': {
                    'int_value': 3
                }
            }
        }

        annotation_attributes = {
            'attributeMap': {
                'annotation_bool': {
                    'bool_value': True
                },
                'annotation_string': {
                    'string_value': {
                        'truncated_byte_count': 0,
                        'value': 'annotation_test'
                    },
                },
                'key_float': {
                    'float_value': .3  #omit
                }
            }
        }

        link_attributes = {'key_bool': {'bool_value': True}}

        time_events = {
            'timeEvent': [{
                'time': '2017-08-15T18:02:26.071158Z',
                'annotation': {
                    'description': 'First annotation',
                    'attributes': annotation_attributes
                },
                'message_event': {
                    'type': 'new_event',
                    'id': 23232
                }
            }]
        }

        links = {
            'link': [{
                'trace_id': trace_id,
                'span_id': span_id,
                'type': link_module.Type.CHILD_LINKED_SPAN,
                'attributes': link_attributes
            }, {
                'trace_id': trace_id,
                'span_id': span_id,
                'type': link_module.Type.PARENT_LINKED_SPAN,
                'attributes': link_attributes
            }, {
                'trace_id': trace_id,
                'span_id': span_id,
                'type': link_module.Type.TYPE_UNSPECIFIED,
                'attributes': link_attributes
            }]
        }

        status = {'code': 200, 'message': 'success'}

        start_time = '2017-08-15T18:02:26.071158Z'
        end_time = '2017-08-15T18:02:36.071158Z'

        trace = {
            'spans': [{
                'name': 'test1',
                'spanId': span_id,
                'startTime': start_time,
                'endTime': end_time,
                'parentSpanId': parent_span_id,
                'attributes': attributes,
                'childSpanCount': 0,
                'spanKind': 0,
                'timeEvents': time_events,
                'links': links,
                'status': status,
                'context': None
            }, {
                'status': None,
                'startTime': start_time,
                'endTime': end_time,
                'context': {
                    'traceOptions': '1'
                }
            }],
            'traceId': trace_id
        }

        exporter = jaeger_exporter.JaegerExporter()

        spans = exporter.translate_to_jaeger(trace)
        expected_spans = [
            jaeger.Span(
                traceIdHigh=1846305573,
                traceIdLow=2112048274,
                spanId=7929822056569588882,
                parentSpanId=1229782938247303441,
                operationName='test1',
                startTime=1502820146000,
                duration=10000,
                tags=[
                    jaeger.Tag(
                        key='key_bool',
                        vType=jaeger.TagType.BOOL,
                        vBool=False),
                    jaeger.Tag(
                        key='key_string',
                        vType=jaeger.TagType.STRING,
                        vStr='hello_world'),
                    jaeger.Tag(
                        key='key_int',
                        vType=jaeger.TagType.LONG,
                        vLong=3),
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
                        traceIdHigh=1846305573,
                        traceIdLow=2112048274,
                        spanId=7929822056569588882),
                    jaeger.SpanRef(
                        refType=jaeger.SpanRefType.FOLLOWS_FROM,
                        traceIdHigh=1846305573,
                        traceIdLow=2112048274,
                        spanId=7929822056569588882),
                    jaeger.SpanRef(
                        refType=None,
                        traceIdHigh=1846305573,
                        traceIdLow=2112048274,
                        spanId=7929822056569588882)
                ],
                logs=[
                    jaeger.Log(
                        timestamp=1502820146000,
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
                                key='message',
                                vType=jaeger.TagType.STRING,
                                vStr='First annotation')
                        ])
                ]),
            jaeger.Span(
                traceIdHigh=1846305573,
                traceIdLow=2112048274,
                startTime=1502820146000,
                duration=10000,
                flags=1)
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
        listsEqual(
            span.get('references'), expected_span.get('references'))
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

    def test_ignore_incorrect_spans(self):
        exporter = jaeger_exporter
        span1 = {
            'attributes': {
                'attributeMap': {
                    'string_value': {
                        'truncated_byte_count': 0,
                        'value': 'hello_world'
                    },
                    'bool': False
                }
            }
        }
        self.assertEqual(exporter._extract_tags(span1), [])

        span2 = {
            'timeEvents': {
                'timeEvent': [{
                    'time': '2017-08-15T18:02:26.071158Z',
                    'annotation': None,
                    'message_event': {
                        'type': 'new_event',
                        'id': 23232
                    }
                }]
            }
        }
        self.assertEqual(exporter._extract_logs_from_span(span2), [])

        span3 = {'links': {'link': ['link1', 'link2']}}
        self.assertEqual(exporter._extract_refs_from_span(span3), [])


class MockBatch(object):
    def write(self, iprot):
        return None


class MockTransport(object):
    def __init__(self, exporter=None, uri_or_host=None):
        self.export_called = False
        self.exporter = exporter
        self.code = 200
        self.message = 'success'
        self.uri_or_host = uri_or_host
        self.scheme = 'http'

    def export(self, trace):
        self.export_called = True

    def close(self):
        return None


class MockClient(object):
    def __init__(self, iprot=None):
        self.emit_called = False
        self.iprot = iprot

    def emitBatch(self, batch):
        self.emit_called = True

    def submitBatches(self, batches):
        return None
