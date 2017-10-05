# Copyright 2017, OpenCensus Authors
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


from opencensus.trace.reporters import zipkin_reporter


class TestZipkinReporter(unittest.TestCase):

    def test_constructor(self):
        service_name = 'my_service'
        host_name = '0.0.0.0'
        port = 2333
        endpoint = '/api/v2/test'

        reporter = zipkin_reporter.ZipkinReporter(
            service_name=service_name,
            host_name=host_name,
            port=port,
            endpoint=endpoint)

        expected_url = 'http://0.0.0.0:2333/api/v2/test'

        self.assertEqual(reporter.service_name, service_name)
        self.assertEqual(reporter.host_name, host_name)
        self.assertEqual(reporter.port, port)
        self.assertEqual(reporter.endpoint, endpoint)
        self.assertEqual(reporter.url, expected_url)

    @mock.patch('requests.post')
    @mock.patch.object(zipkin_reporter.ZipkinReporter,
                'translate_to_zipkin')
    def test_report_succeeded(self, translate_mock, requests_mock):
        import json

        trace = {'test': 'this_is_for_test'}

        reporter = zipkin_reporter.ZipkinReporter(service_name='my_service')
        response = mock.Mock()
        response.status_code = 202
        requests_mock.return_value = response
        translate_mock.return_value = trace
        reporter.report(trace)

        requests_mock.assert_called_once_with(
            url=reporter.url,
            data=json.dumps(trace),
            headers=zipkin_reporter.ZIPKIN_HEADERS)

    @mock.patch('requests.post')
    @mock.patch.object(zipkin_reporter.ZipkinReporter,
                'translate_to_zipkin')
    def test_report_failed(self, translate_mock, requests_mock):
        import json

        trace = {'test': 'this_is_for_test'}

        reporter = zipkin_reporter.ZipkinReporter(service_name='my_service')
        response = mock.Mock()
        response.status_code = 400
        requests_mock.return_value = response
        translate_mock.return_value = trace
        reporter.report(trace)

        requests_mock.assert_called_once_with(
            url=reporter.url,
            data=json.dumps(trace),
            headers=zipkin_reporter.ZIPKIN_HEADERS)

    def test_translate_to_zipkin_span_kind_none(self):
        span1 = {
            'name': 'child_span',
            'parentSpanId': 1111111111,
            'spanId': 1234567890,
            'startTime': '2017-08-15T18:02:26.071158Z',
            'endTime': '2017-08-15T18:02:36.071158Z',
            'labels': {
                'key': 'test_key',
                'value': 'test_value',
            },
        }

        span2 = {
            'name': 'child_span',
            'kind': 0,
            'parentSpanId': 1111111111,
            'spanId': 1234567890,
            'startTime': '2017-08-15T18:02:26.071158Z',
            'endTime': '2017-08-15T18:02:36.071158Z',
            'labels': {
                'key': 'test_key',
                'value': 'test_value',
            },
        }

        span3 = {
            'name': 'child_span',
            'kind': 1,
            'spanId': 1234567890,
            'startTime': '2017-08-15T18:02:26.071158Z',
            'endTime': '2017-08-15T18:02:36.071158Z',
            'labels': {
                'key': 'test_key',
                'value': 'test_value',
            },
        }

        trace_id = '6e0c63257de34c92bf9efcd03927272e'
        spans = [span1, span2, span3]

        local_endpoint = {
            'serviceName': 'my_service',
            'ipv4': 'localhost',
            'port': 9411,
        }

        expected_zipkin_spans = [
            {
                'traceId': '6e0c63257de34c92bf9efcd03927272e',
                'id': '1234567890',
                'parentId': '1111111111',
                'name': 'child_span',
                'timestamp': 1502820146000000,
                'duration': 10000000,
                'localEndpoint': local_endpoint,
                'tags': {
                    'key': 'test_key',
                    'value': 'test_value',
                },
            },
            {
                'traceId': '6e0c63257de34c92bf9efcd03927272e',
                'id': '1234567890',
                'parentId': '1111111111',
                'name': 'child_span',
                'timestamp': 1502820146000000,
                'duration': 10000000,
                'localEndpoint': local_endpoint,
                'tags': {
                    'key': 'test_key',
                    'value': 'test_value',
                },
            },
            {
                'traceId': '6e0c63257de34c92bf9efcd03927272e',
                'id': '1234567890',
                'name': 'child_span',
                'timestamp': 1502820146000000,
                'duration': 10000000,
                'localEndpoint': local_endpoint,
                'tags': {
                    'key': 'test_key',
                    'value': 'test_value',
                },
                'kind': 'SERVER',
            }
        ]

        reporter = zipkin_reporter.ZipkinReporter(service_name='my_service')
        zipkin_spans = reporter.translate_to_zipkin(
            trace_id=trace_id,
            spans=spans)

        self.assertEqual(zipkin_spans, expected_zipkin_spans)
