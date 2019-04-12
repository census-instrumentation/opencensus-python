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

import mock
import unittest
from opencensus.ext.azure import trace_exporter


class TestAzureExporter(unittest.TestCase):
    def test_export(self):
        exporter = trace_exporter.AzureExporter()
        exporter.transport = MockTransport()
        exporter.export(None)
        self.assertTrue(exporter.transport.export_called)

    @mock.patch('requests.post', return_value=mock.Mock())
    def test_emit(self, request_mock):
        exporter = trace_exporter.AzureExporter()
        exporter.transport = MockTransport()
        exporter.emit([])

    def test_span_data_to_envelope(self):
        from opencensus.ext.azure.common import Options
        from opencensus.trace.span import SpanKind
        from opencensus.trace.span_context import SpanContext
        from opencensus.trace.span_data import SpanData
        from opencensus.trace.trace_options import TraceOptions
        from opencensus.trace.tracestate import Tracestate

        instrumentation_key = '12345678-1234-5678-abcd-12345678abcd'
        exporter = trace_exporter.AzureExporter(
            Options(instrumentation_key=instrumentation_key),
        )

        # SpanKind.CLIENT HTTP
        envelope = exporter.span_data_to_envelope(SpanData(
            name='test',
            context=SpanContext(
                trace_id='6e0c63257de34c90bf9efcd03927272e',
                span_id='6e0c63257de34c91',
                trace_options=TraceOptions('1'),
                tracestate=Tracestate(),
                from_header=False,
            ),
            span_id='6e0c63257de34c92',
            parent_span_id='6e0c63257de34c93',
            attributes={
                'http.method': 'GET',
                'http.url': 'https://www.wikipedia.org/wiki/Rabbit',
                'http.status_code': 200,
            },
            start_time='2010-10-24T07:28:38.123456Z',
            end_time='2010-10-24T07:28:38.234567Z',
            stack_trace=None,
            links=None,
            status=None,
            time_events=None,
            same_process_as_parent_span=None,
            child_span_count=None,
            span_kind=SpanKind.CLIENT,
        ))
        self.assertEqual(
            envelope.iKey,
            '12345678-1234-5678-abcd-12345678abcd')
        self.assertEqual(
            envelope.name,
            'Microsoft.ApplicationInsights.RemoteDependency')
        self.assertEqual(
            envelope.tags['ai.operation.parentId'],
            '|6e0c63257de34c90bf9efcd03927272e.6e0c63257de34c93.')
        self.assertEqual(
            envelope.tags['ai.operation.id'],
            '6e0c63257de34c90bf9efcd03927272e')
        self.assertEqual(
            envelope.time,
            '2010-10-24T07:28:38.123456Z')
        self.assertEqual(
            envelope.data.baseData.name,
            'www.wikipedia.org')
        self.assertEqual(
            envelope.data.baseData.id,
            '|6e0c63257de34c90bf9efcd03927272e.6e0c63257de34c92.')
        self.assertEqual(
            envelope.data.baseData.resultCode,
            '200')
        self.assertEqual(
            envelope.data.baseData.duration,
            '0.00:00:00.111')
        self.assertEqual(
            envelope.data.baseData.type,
            'HTTP')
        self.assertEqual(
            envelope.data.baseType,
            'RemoteDependencyData')

        # SpanKind.CLIENT unknown type
        envelope = exporter.span_data_to_envelope(SpanData(
            name='test',
            context=SpanContext(
                trace_id='6e0c63257de34c90bf9efcd03927272e',
                span_id='6e0c63257de34c91',
                trace_options=TraceOptions('1'),
                tracestate=Tracestate(),
                from_header=False,
            ),
            span_id='6e0c63257de34c92',
            parent_span_id='6e0c63257de34c93',
            attributes={},
            start_time='2010-10-24T07:28:38.123456Z',
            end_time='2010-10-24T07:28:38.234567Z',
            stack_trace=None,
            links=None,
            status=None,
            time_events=None,
            same_process_as_parent_span=None,
            child_span_count=None,
            span_kind=SpanKind.CLIENT,
        ))
        self.assertEqual(
            envelope.iKey,
            '12345678-1234-5678-abcd-12345678abcd')
        self.assertEqual(
            envelope.name,
            'Microsoft.ApplicationInsights.RemoteDependency')
        self.assertEqual(
            envelope.tags['ai.operation.parentId'],
            '|6e0c63257de34c90bf9efcd03927272e.6e0c63257de34c93.')
        self.assertEqual(
            envelope.tags['ai.operation.id'],
            '6e0c63257de34c90bf9efcd03927272e')
        self.assertEqual(
            envelope.time,
            '2010-10-24T07:28:38.123456Z')
        self.assertEqual(
            envelope.data.baseData.name,
            'test')
        self.assertEqual(
            envelope.data.baseData.id,
            '|6e0c63257de34c90bf9efcd03927272e.6e0c63257de34c92.')
        self.assertEqual(
            envelope.data.baseData.duration,
            '0.00:00:00.111')
        self.assertEqual(
            envelope.data.baseData.type,
            'HTTP')
        self.assertEqual(
            envelope.data.baseType,
            'RemoteDependencyData')

        # SpanKind.SERVER HTTP
        envelope = exporter.span_data_to_envelope(SpanData(
            name='test',
            context=SpanContext(
                trace_id='6e0c63257de34c90bf9efcd03927272e',
                span_id='6e0c63257de34c91',
                trace_options=TraceOptions('1'),
                tracestate=Tracestate(),
                from_header=False,
            ),
            span_id='6e0c63257de34c92',
            parent_span_id='6e0c63257de34c93',
            attributes={
                'http.method': 'GET',
                'http.url': 'https://www.wikipedia.org/wiki/Rabbit',
                'http.status_code': 200,
            },
            start_time='2010-10-24T07:28:38.123456Z',
            end_time='2010-10-24T07:28:38.234567Z',
            stack_trace=None,
            links=None,
            status=None,
            time_events=None,
            same_process_as_parent_span=None,
            child_span_count=None,
            span_kind=SpanKind.SERVER,
        ))
        self.assertEqual(
            envelope.iKey,
            '12345678-1234-5678-abcd-12345678abcd')
        self.assertEqual(
            envelope.name,
            'Microsoft.ApplicationInsights.Request')
        self.assertEqual(
            envelope.tags['ai.operation.parentId'],
            '|6e0c63257de34c90bf9efcd03927272e.6e0c63257de34c93.')
        self.assertEqual(
            envelope.tags['ai.operation.id'],
            '6e0c63257de34c90bf9efcd03927272e')
        self.assertEqual(
            envelope.time,
            '2010-10-24T07:28:38.123456Z')
        self.assertEqual(
            envelope.data.baseData.id,
            '|6e0c63257de34c90bf9efcd03927272e.6e0c63257de34c92.')
        self.assertEqual(
            envelope.data.baseData.duration,
            '0.00:00:00.111')
        self.assertEqual(
            envelope.data.baseData.responseCode,
            '200')
        self.assertEqual(
            envelope.data.baseData.name,
            'GET https://www.wikipedia.org/wiki/Rabbit')
        self.assertEqual(
            envelope.data.baseData.url,
            'https://www.wikipedia.org/wiki/Rabbit')
        self.assertEqual(
            envelope.data.baseType,
            'RequestData')

        # SpanKind.SERVER unknown type
        envelope = exporter.span_data_to_envelope(SpanData(
            name='test',
            context=SpanContext(
                trace_id='6e0c63257de34c90bf9efcd03927272e',
                span_id='6e0c63257de34c91',
                trace_options=TraceOptions('1'),
                tracestate=Tracestate(),
                from_header=False,
            ),
            span_id='6e0c63257de34c92',
            parent_span_id='6e0c63257de34c93',
            attributes={},
            start_time='2010-10-24T07:28:38.123456Z',
            end_time='2010-10-24T07:28:38.234567Z',
            stack_trace=None,
            links=None,
            status=None,
            time_events=None,
            same_process_as_parent_span=None,
            child_span_count=None,
            span_kind=SpanKind.SERVER,
        ))
        self.assertEqual(
            envelope.iKey,
            '12345678-1234-5678-abcd-12345678abcd')
        self.assertEqual(
            envelope.name,
            'Microsoft.ApplicationInsights.Request')
        self.assertEqual(
            envelope.tags['ai.operation.parentId'],
            '|6e0c63257de34c90bf9efcd03927272e.6e0c63257de34c93.')
        self.assertEqual(
            envelope.tags['ai.operation.id'],
            '6e0c63257de34c90bf9efcd03927272e')
        self.assertEqual(
            envelope.time,
            '2010-10-24T07:28:38.123456Z')
        self.assertEqual(
            envelope.data.baseData.id,
            '|6e0c63257de34c90bf9efcd03927272e.6e0c63257de34c92.')
        self.assertEqual(
            envelope.data.baseData.duration,
            '0.00:00:00.111')
        self.assertEqual(
            envelope.data.baseType,
            'RequestData')

        # SpanKind.UNSPECIFIED
        envelope = exporter.span_data_to_envelope(SpanData(
            name='test',
            context=SpanContext(
                trace_id='6e0c63257de34c90bf9efcd03927272e',
                span_id='6e0c63257de34c91',
                trace_options=TraceOptions('1'),
                tracestate=Tracestate(),
                from_header=False,
            ),
            span_id='6e0c63257de34c92',
            parent_span_id=None,
            attributes={'key1': 'value1'},
            start_time='2010-10-24T07:28:38.123456Z',
            end_time='2010-10-24T07:28:38.234567Z',
            stack_trace=None,
            links=None,
            status=None,
            time_events=None,
            same_process_as_parent_span=None,
            child_span_count=None,
            span_kind=SpanKind.UNSPECIFIED,
        ))
        self.assertEqual(
            envelope.iKey,
            '12345678-1234-5678-abcd-12345678abcd')
        self.assertEqual(
            envelope.name,
            'Microsoft.ApplicationInsights.RemoteDependency')
        self.assertRaises(
            KeyError,
            lambda: envelope.tags['ai.operation.parentId'])
        self.assertEqual(
            envelope.tags['ai.operation.id'],
            '6e0c63257de34c90bf9efcd03927272e')
        self.assertEqual(
            envelope.time,
            '2010-10-24T07:28:38.123456Z')
        self.assertEqual(
            envelope.data.baseData.name,
            'test')
        self.assertEqual(
            envelope.data.baseData.duration,
            '0.00:00:00.111')
        self.assertEqual(
            envelope.data.baseData.id,
            '|6e0c63257de34c90bf9efcd03927272e.6e0c63257de34c92.')
        self.assertEqual(
            envelope.data.baseData.type,
            'INPROC')
        self.assertEqual(
            envelope.data.baseType,
            'RemoteDependencyData')


class MockTransport(object):
    def __init__(self, exporter=None):
        self.export_called = False
        self.exporter = exporter

    def export(self, datas):
        self.export_called = True
