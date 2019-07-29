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

import json
import mock
import os
import shutil
import unittest

from opencensus.ext.azure import trace_exporter

TEST_FOLDER = os.path.abspath('.test.exporter')


def setUpModule():
    os.makedirs(TEST_FOLDER)


def tearDownModule():
    shutil.rmtree(TEST_FOLDER)


def throw(exc_type, *args, **kwargs):
    def func(*_args, **_kwargs):
        raise exc_type(*args, **kwargs)
    return func


class TestAzureExporter(unittest.TestCase):
    def test_ctor(self):
        from opencensus.ext.azure.common import Options
        instrumentation_key = Options._default.instrumentation_key
        Options._default.instrumentation_key = None
        self.assertRaises(ValueError, lambda: trace_exporter.AzureExporter())
        Options._default.instrumentation_key = instrumentation_key

    @mock.patch('requests.post', return_value=mock.Mock())
    def test_emit_empty(self, request_mock):
        exporter = trace_exporter.AzureExporter(
            instrumentation_key='12345678-1234-5678-abcd-12345678abcd',
            storage_path=os.path.join(TEST_FOLDER, self.id()),
        )
        exporter.emit([])
        self.assertEqual(len(os.listdir(exporter.storage.path)), 0)
        exporter._stop()

    @mock.patch('opencensus.ext.azure.trace_exporter.logger')
    def test_emit_exception(self, mock_logger):
        exporter = trace_exporter.AzureExporter(
            instrumentation_key='12345678-1234-5678-abcd-12345678abcd',
            storage_path=os.path.join(TEST_FOLDER, self.id()),
        )
        exporter.emit([1, 2, 3])
        mock_logger.exception.assert_called()
        exporter._stop()

    @mock.patch('opencensus.ext.azure.trace_exporter.AzureExporter.span_data_to_envelope')  # noqa: E501
    def test_emit_failure(self, span_data_to_envelope_mock):
        span_data_to_envelope_mock.return_value = ['bar']
        exporter = trace_exporter.AzureExporter(
            instrumentation_key='12345678-1234-5678-abcd-12345678abcd',
            storage_path=os.path.join(TEST_FOLDER, self.id()),
        )
        with mock.patch('opencensus.ext.azure.trace_exporter.AzureExporter._transmit') as transmit:  # noqa: E501
            transmit.return_value = 10
            exporter.emit(['foo'])
        self.assertEqual(len(os.listdir(exporter.storage.path)), 1)
        self.assertIsNone(exporter.storage.get())
        exporter._stop()

    @mock.patch('opencensus.ext.azure.trace_exporter.AzureExporter.span_data_to_envelope')  # noqa: E501
    def test_emit_success(self, span_data_to_envelope_mock):
        span_data_to_envelope_mock.return_value = ['bar']
        exporter = trace_exporter.AzureExporter(
            instrumentation_key='12345678-1234-5678-abcd-12345678abcd',
            max_batch_size=1,
            storage_path=os.path.join(TEST_FOLDER, self.id()),
        )
        with mock.patch('opencensus.ext.azure.trace_exporter.AzureExporter._transmit') as transmit:  # noqa: E501
            transmit.return_value = 0
            exporter.emit([])
            exporter.emit(['foo'])
            self.assertEqual(len(os.listdir(exporter.storage.path)), 0)
            exporter.emit(['foo'], mock.Mock())
            self.assertEqual(len(os.listdir(exporter.storage.path)), 0)
        exporter._stop()

    def test_span_data_to_envelope(self):
        from opencensus.trace.span import SpanKind
        from opencensus.trace.span_context import SpanContext
        from opencensus.trace.span_data import SpanData
        from opencensus.trace.trace_options import TraceOptions
        from opencensus.trace.tracestate import Tracestate

        exporter = trace_exporter.AzureExporter(
            instrumentation_key='12345678-1234-5678-abcd-12345678abcd',
            storage_path=os.path.join(TEST_FOLDER, self.id()),
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
            annotations=None,
            message_events=None,
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
            annotations=None,
            message_events=None,
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

        # SpanKind.SERVER HTTP - 200 request
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
                'http.path': '/wiki/Rabbit',
                'http.route': '/wiki/Rabbit',
                'http.url': 'https://www.wikipedia.org/wiki/Rabbit',
                'http.status_code': 200,
            },
            start_time='2010-10-24T07:28:38.123456Z',
            end_time='2010-10-24T07:28:38.234567Z',
            stack_trace=None,
            links=None,
            status=None,
            annotations=None,
            message_events=None,
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
            envelope.tags['ai.operation.name'],
            'GET /wiki/Rabbit')
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
            'GET /wiki/Rabbit')
        self.assertEqual(
            envelope.data.baseData.success,
            True)
        self.assertEqual(
            envelope.data.baseData.url,
            'https://www.wikipedia.org/wiki/Rabbit')
        self.assertEqual(
            envelope.data.baseType,
            'RequestData')

        # SpanKind.SERVER HTTP - Failed request
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
                'http.path': '/wiki/Rabbit',
                'http.route': '/wiki/Rabbit',
                'http.url': 'https://www.wikipedia.org/wiki/Rabbit',
                'http.status_code': 400,
            },
            start_time='2010-10-24T07:28:38.123456Z',
            end_time='2010-10-24T07:28:38.234567Z',
            stack_trace=None,
            links=None,
            status=None,
            annotations=None,
            message_events=None,
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
            envelope.tags['ai.operation.name'],
            'GET /wiki/Rabbit')
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
            '400')
        self.assertEqual(
            envelope.data.baseData.name,
            'GET /wiki/Rabbit')
        self.assertEqual(
            envelope.data.baseData.success,
            False)
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
            annotations=None,
            message_events=None,
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
            annotations=None,
            message_events=None,
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

        exporter._stop()

    def test_transmission_nothing(self):
        exporter = trace_exporter.AzureExporter(
            instrumentation_key='12345678-1234-5678-abcd-12345678abcd',
            storage_path=os.path.join(TEST_FOLDER, self.id()),
        )
        with mock.patch('requests.post') as post:
            post.return_value = None
            exporter._transmit_from_storage()
        exporter._stop()

    def test_transmission_request_exception(self):
        exporter = trace_exporter.AzureExporter(
            instrumentation_key='12345678-1234-5678-abcd-12345678abcd',
            storage_path=os.path.join(TEST_FOLDER, self.id()),
        )
        exporter.storage.put([1, 2, 3])
        with mock.patch('requests.post', throw(Exception)):
            exporter._transmit_from_storage()
        self.assertIsNone(exporter.storage.get())
        self.assertEqual(len(os.listdir(exporter.storage.path)), 1)
        exporter._stop()

    @mock.patch('requests.post', return_value=mock.Mock())
    def test_transmission_lease_failure(self, requests_mock):
        requests_mock.return_value = MockResponse(200, 'unknown')
        exporter = trace_exporter.AzureExporter(
            instrumentation_key='12345678-1234-5678-abcd-12345678abcd',
            storage_path=os.path.join(TEST_FOLDER, self.id()),
        )
        exporter.storage.put([1, 2, 3])
        with mock.patch('opencensus.ext.azure.common.storage.LocalFileBlob.lease') as lease:  # noqa: E501
            lease.return_value = False
            exporter._transmit_from_storage()
        self.assertTrue(exporter.storage.get())
        exporter._stop()

    def test_transmission_response_exception(self):
        exporter = trace_exporter.AzureExporter(
            instrumentation_key='12345678-1234-5678-abcd-12345678abcd',
            storage_path=os.path.join(TEST_FOLDER, self.id()),
        )
        exporter.storage.put([1, 2, 3])
        with mock.patch('requests.post') as post:
            post.return_value = MockResponse(200, None)
            del post.return_value.text
            exporter._transmit_from_storage()
        self.assertIsNone(exporter.storage.get())
        self.assertEqual(len(os.listdir(exporter.storage.path)), 0)
        exporter._stop()

    def test_transmission_200(self):
        exporter = trace_exporter.AzureExporter(
            instrumentation_key='12345678-1234-5678-abcd-12345678abcd',
            storage_path=os.path.join(TEST_FOLDER, self.id()),
        )
        exporter.storage.put([1, 2, 3])
        exporter.storage.put([1, 2, 3])
        with mock.patch('requests.post') as post:
            post.return_value = MockResponse(200, 'unknown')
            exporter._transmit_from_storage()
        self.assertIsNone(exporter.storage.get())
        self.assertEqual(len(os.listdir(exporter.storage.path)), 0)
        exporter._stop()

    def test_transmission_206(self):
        exporter = trace_exporter.AzureExporter(
            instrumentation_key='12345678-1234-5678-abcd-12345678abcd',
            storage_path=os.path.join(TEST_FOLDER, self.id()),
        )
        exporter.storage.put([1, 2, 3])
        with mock.patch('requests.post') as post:
            post.return_value = MockResponse(206, 'unknown')
            exporter._transmit_from_storage()
        self.assertIsNone(exporter.storage.get())
        self.assertEqual(len(os.listdir(exporter.storage.path)), 1)
        exporter._stop()

    def test_transmission_206_500(self):
        exporter = trace_exporter.AzureExporter(
            instrumentation_key='12345678-1234-5678-abcd-12345678abcd',
            storage_path=os.path.join(TEST_FOLDER, self.id()),
        )
        exporter.storage.put([1, 2, 3, 4, 5])
        with mock.patch('requests.post') as post:
            post.return_value = MockResponse(206, json.dumps({
                'itemsReceived': 5,
                'itemsAccepted': 3,
                'errors': [
                    {
                        'index': 0,
                        'statusCode': 400,
                        'message': '',
                    },
                    {
                        'index': 2,
                        'statusCode': 500,
                        'message': 'Internal Server Error',
                    },
                ],
            }))
            exporter._transmit_from_storage()
        self.assertEqual(len(os.listdir(exporter.storage.path)), 1)
        self.assertEqual(exporter.storage.get().get(), (3,))
        exporter._stop()

    def test_transmission_206_nothing_to_retry(self):
        exporter = trace_exporter.AzureExporter(
            instrumentation_key='12345678-1234-5678-abcd-12345678abcd',
            storage_path=os.path.join(TEST_FOLDER, self.id()),
        )
        exporter.storage.put([1, 2, 3])
        with mock.patch('requests.post') as post:
            post.return_value = MockResponse(206, json.dumps({
                'itemsReceived': 3,
                'itemsAccepted': 2,
                'errors': [
                    {
                        'index': 0,
                        'statusCode': 400,
                        'message': '',
                    },
                ],
            }))
            exporter._transmit_from_storage()
        self.assertEqual(len(os.listdir(exporter.storage.path)), 0)
        exporter._stop()

    def test_transmission_206_bogus(self):
        exporter = trace_exporter.AzureExporter(
            instrumentation_key='12345678-1234-5678-abcd-12345678abcd',
            storage_path=os.path.join(TEST_FOLDER, self.id()),
        )
        exporter.storage.put([1, 2, 3, 4, 5])
        with mock.patch('requests.post') as post:
            post.return_value = MockResponse(206, json.dumps({
                'itemsReceived': 5,
                'itemsAccepted': 3,
                'errors': [
                    {
                        'foo': 0,
                        'bar': 1,
                    },
                ],
            }))
            exporter._transmit_from_storage()
        self.assertIsNone(exporter.storage.get())
        self.assertEqual(len(os.listdir(exporter.storage.path)), 0)
        exporter._stop()

    def test_transmission_400(self):
        exporter = trace_exporter.AzureExporter(
            instrumentation_key='12345678-1234-5678-abcd-12345678abcd',
            storage_path=os.path.join(TEST_FOLDER, self.id()),
        )
        exporter.storage.put([1, 2, 3])
        with mock.patch('requests.post') as post:
            post.return_value = MockResponse(400, '{}')
            exporter._transmit_from_storage()
        self.assertEqual(len(os.listdir(exporter.storage.path)), 0)
        exporter._stop()

    def test_transmission_500(self):
        exporter = trace_exporter.AzureExporter(
            instrumentation_key='12345678-1234-5678-abcd-12345678abcd',
            storage_path=os.path.join(TEST_FOLDER, self.id()),
        )
        exporter.storage.put([1, 2, 3])
        with mock.patch('requests.post') as post:
            post.return_value = MockResponse(500, '{}')
            exporter._transmit_from_storage()
        self.assertIsNone(exporter.storage.get())
        self.assertEqual(len(os.listdir(exporter.storage.path)), 1)
        exporter._stop()


class MockResponse(object):
    def __init__(self, status_code, text):
        self.status_code = status_code
        self.text = text
