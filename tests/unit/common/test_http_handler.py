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
import socket
import mock
import json

from opencensus.common.http_handler import get_request

try:
    # For Python 3.0 and later
    from urllib.error import HTTPError, URLError
    from io import StringIO
except ImportError:
    # Fall back to Python 2's urllib2
    from urllib2 import HTTPError, URLError
    from StringIO import StringIO


class TestHttpHandler(unittest.TestCase):
    TEST_URL = 'https://localhost:8080/metadata'

    @mock.patch('opencensus.common.http_handler.Request')
    @mock.patch('opencensus.common.http_handler.urlopen')
    def test_urlopen(self, urlopen_mock, request_mock):
        mocked_response = {
            'availabilityZone': 'us-west-2b',
            'instanceId': 'i-1234567890abcdef0',
            'imageId': 'ami-5fb8c835',
            'privateIp': '10.158.112.84',
            'pendingTime': '2016-11-19T16:32:11Z',
            'accountId': '12345678901',
            'region': 'us-west-2',
            'marketplaceProductCodes': ["1abc2defghijklm3nopqrs4tu"],
            'instanceType': 't2.micro',
            'version': '2017-09-30',
            'architecture': 'x86_64',
        }

        urlopen_mock.return_value = StringIO(json.dumps(mocked_response))
        data = get_request(self.TEST_URL)
        self.assertIn('availabilityZone', data)
        self.assertEqual(urlopen_mock.call_count, 1)

    @mock.patch('opencensus.common.http_handler.Request')
    @mock.patch('opencensus.common.http_handler.urlopen')
    def test_urlopen_with_headers(self, urlopen_mock, request_mock):
        mocked_response = {
            'availabilityZone': 'us-west-2b',
            'instanceId': 'i-1234567890abcdef0',
            'imageId': 'ami-5fb8c835',
            'privateIp': '10.158.112.84',
            'pendingTime': '2016-11-19T16:32:11Z',
            'accountId': '123456789012',
            'region': 'us-west-2',
            'marketplaceProductCodes': ["1abc2defghijklm3nopqrs4tu"],
            'instanceType': 't2.micro',
            'version': '2017-09-30',
            'architecture': 'x86_64',
        }
        headers = {'accept': 'application/json', 'Metadata-Flavor': 'Google'}

        urlopen_mock.return_value = StringIO(json.dumps(mocked_response))
        data = get_request(self.TEST_URL, headers)
        self.assertIn('availabilityZone', data)
        self.assertEqual(urlopen_mock.call_count, 1)

    def test_urlopen_requests_on_urlerror(self):
        def raise_urlerror(req, timeout):
            raise URLError('URL Error message')

        with mock.patch(
                'opencensus.common.http_handler.urlopen') as urlopen_mock:
            urlopen_mock.side_effect = raise_urlerror
            self.assertIsNone(get_request(self.TEST_URL))

    def test_urlopen_requests_on_httperror(self):
        def raise_httperror(req, timeout):
            raise HTTPError(
                url='http://127.0.0.1',
                code=400,
                msg='Bad request',
                hdrs=None,
                fp=None)

        with mock.patch(
                'opencensus.common.http_handler.urlopen') as urlopen_mock:
            urlopen_mock.side_effect = raise_httperror
            self.assertIsNone(get_request(self.TEST_URL))

    def test_urlopen_requests_on_sockettimeout(self):
        def raise_sockettimeout(req, timeout):
            raise socket.timeout('URL Timeout message')

        with mock.patch(
                'opencensus.common.http_handler.urlopen') as urlopen_mock:
            urlopen_mock.side_effect = raise_sockettimeout
            self.assertIsNone(get_request(self.TEST_URL))
