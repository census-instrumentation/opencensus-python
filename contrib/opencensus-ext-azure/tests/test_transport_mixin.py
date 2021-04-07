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
import os
import shutil
import unittest

import mock
import requests

from azure.core.exceptions import ClientAuthenticationError
from azure.identity._exceptions import CredentialUnavailableError
from opencensus.ext.azure.common import Options
from opencensus.ext.azure.common.storage import LocalFileStorage
from opencensus.ext.azure.common.transport import TransportMixin

TEST_FOLDER = os.path.abspath('.test.storage')


def setUpModule():
    os.makedirs(TEST_FOLDER)


def tearDownModule():
    shutil.rmtree(TEST_FOLDER)


def throw(exc_type, *args, **kwargs):
    def func(*_args, **_kwargs):
        raise exc_type(*args, **kwargs)
    return func


class MockResponse(object):
    def __init__(self, status_code, text):
        self.status_code = status_code
        self.text = text


# pylint: disable=W0212
class TestTransportMixin(unittest.TestCase):
    def test_transmission_nothing(self):
        mixin = TransportMixin()
        with LocalFileStorage(os.path.join(TEST_FOLDER, self.id())) as stor:
            mixin.storage = stor
            with mock.patch('requests.post') as post:
                post.return_value = None
                mixin._transmit_from_storage()

    def test_transmission_pre_timeout(self):
        mixin = TransportMixin()
        mixin.options = Options()
        with LocalFileStorage(os.path.join(TEST_FOLDER, self.id())) as stor:
            mixin.storage = stor
            mixin.storage.put([1, 2, 3])
            with mock.patch('requests.post', throw(requests.Timeout)):
                mixin._transmit_from_storage()
            self.assertIsNone(mixin.storage.get())
            self.assertEqual(len(os.listdir(mixin.storage.path)), 1)

    def test_transmission_pre_req_exception(self):
        mixin = TransportMixin()
        mixin.options = Options()
        with LocalFileStorage(os.path.join(TEST_FOLDER, self.id())) as stor:
            mixin.storage = stor
            mixin.storage.put([1, 2, 3])
            with mock.patch('requests.post', throw(requests.RequestException)):
                mixin._transmit_from_storage()
            self.assertIsNone(mixin.storage.get())
            self.assertEqual(len(os.listdir(mixin.storage.path)), 1)

    def test_transmission_cred_exception(self):
        mixin = TransportMixin()
        mixin.options = Options()
        with LocalFileStorage(os.path.join(TEST_FOLDER, self.id())) as stor:
            mixin.storage = stor
            mixin.storage.put([1, 2, 3])
            with mock.patch('requests.post', throw(CredentialUnavailableError)):
                mixin._transmit_from_storage()
            self.assertIsNone(mixin.storage.get())
            self.assertEqual(len(os.listdir(mixin.storage.path)), 0)

    def test_transmission_client_exception(self):
        mixin = TransportMixin()
        mixin.options = Options()
        with LocalFileStorage(os.path.join(TEST_FOLDER, self.id())) as stor:
            mixin.storage = stor
            mixin.storage.put([1, 2, 3])
            with mock.patch('requests.post', throw(ClientAuthenticationError)):
                mixin._transmit_from_storage()
            self.assertIsNone(mixin.storage.get())
            self.assertEqual(len(os.listdir(mixin.storage.path)), 1)

    def test_transmission_pre_exception(self):
        mixin = TransportMixin()
        mixin.options = Options()
        with LocalFileStorage(os.path.join(TEST_FOLDER, self.id())) as stor:
            mixin.storage = stor
            mixin.storage.put([1, 2, 3])
            with mock.patch('requests.post', throw(Exception)):
                mixin._transmit_from_storage()
            self.assertIsNone(mixin.storage.get())
            self.assertEqual(len(os.listdir(mixin.storage.path)), 0)

    @mock.patch('requests.post', return_value=mock.Mock())
    def test_transmission_lease_failure(self, requests_mock):
        requests_mock.return_value = MockResponse(200, 'unknown')
        mixin = TransportMixin()
        mixin.options = Options()
        with LocalFileStorage(os.path.join(TEST_FOLDER, self.id())) as stor:
            mixin.storage = stor
            mixin.storage.put([1, 2, 3])
            with mock.patch(
                'opencensus.ext.azure.common.storage.LocalFileBlob.lease'
            ) as lease:  # noqa: E501
                lease.return_value = False
                mixin._transmit_from_storage()
            self.assertTrue(mixin.storage.get())

    def test_transmission_exception(self):
        mixin = TransportMixin()
        mixin.options = Options()
        with LocalFileStorage(os.path.join(TEST_FOLDER, self.id())) as stor:
            mixin.storage = stor
            mixin.storage.put([1, 2, 3])
            with mock.patch('requests.post') as post:
                post.return_value = MockResponse(200, None)
                del post.return_value.text
                mixin._transmit_from_storage()
            self.assertIsNone(mixin.storage.get())
            self.assertEqual(len(os.listdir(mixin.storage.path)), 0)

    def test_transmission_200(self):
        mixin = TransportMixin()
        mixin.options = Options()
        with LocalFileStorage(os.path.join(TEST_FOLDER, self.id())) as stor:
            mixin.storage = stor
            mixin.storage.put([1, 2, 3])
            mixin.storage.put([1, 2, 3])
            with mock.patch('requests.post') as post:
                post.return_value = MockResponse(200, 'unknown')
                mixin._transmit_from_storage()
            self.assertIsNone(mixin.storage.get())
            self.assertEqual(len(os.listdir(mixin.storage.path)), 0)

    def test_transmission_auth(self):
        mixin = TransportMixin()
        mixin.options = Options()
        credential = mock.Mock()
        mixin.options.credential = credential
        token_mock = mock.Mock()
        token_mock.token = "test_token"
        credential.get_token.return_value = token_mock
        url = 'https://eastus-1.in.applicationinsights.azure.com//v2/track'
        data = '[1, 2, 3]'
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json; charset=utf-8',
            'Authorization': 'Bearer test_token',
        }
        with LocalFileStorage(os.path.join(TEST_FOLDER, self.id())) as stor:
            mixin.storage = stor
            mixin.storage.put([1, 2, 3])
            with mock.patch('requests.post') as post:
                post.return_value = MockResponse(200, 'unknown')
                mixin._transmit_from_storage()
                post.assert_called_with(
                    url=url, data=data, headers=headers, timeout=10.0, proxies={})
            credential.get_token.assert_called_with(
                "https://monitor.azure.com/.default")
            self.assertIsNone(mixin.storage.get())
            self.assertEqual(len(os.listdir(mixin.storage.path)), 0)
            credential.get_token.assert_called_once()

    def test_transmission_206(self):
        mixin = TransportMixin()
        mixin.options = Options()
        with LocalFileStorage(os.path.join(TEST_FOLDER, self.id())) as stor:
            mixin.storage = stor
            mixin.storage.put([1, 2, 3])
            with mock.patch('requests.post') as post:
                post.return_value = MockResponse(206, 'unknown')
                mixin._transmit_from_storage()
            self.assertIsNone(mixin.storage.get())
            self.assertEqual(len(os.listdir(mixin.storage.path)), 1)

    def test_transmission_206_500(self):
        mixin = TransportMixin()
        mixin.options = Options()
        with LocalFileStorage(os.path.join(TEST_FOLDER, self.id())) as stor:
            mixin.storage = stor
            mixin.storage.put([1, 2, 3, 4, 5])
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
                mixin._transmit_from_storage()
            self.assertEqual(len(os.listdir(mixin.storage.path)), 1)
            self.assertEqual(mixin.storage.get().get(), (3,))

    def test_transmission_206_no_retry(self):
        mixin = TransportMixin()
        mixin.options = Options()
        with LocalFileStorage(os.path.join(TEST_FOLDER, self.id())) as stor:
            mixin.storage = stor
            mixin.storage.put([1, 2, 3])
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
                mixin._transmit_from_storage()
            self.assertEqual(len(os.listdir(mixin.storage.path)), 0)

    def test_transmission_206_bogus(self):
        mixin = TransportMixin()
        mixin.options = Options()
        with LocalFileStorage(os.path.join(TEST_FOLDER, self.id())) as stor:
            mixin.storage = stor
            mixin.storage.put([1, 2, 3, 4, 5])
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
                mixin._transmit_from_storage()
            self.assertIsNone(mixin.storage.get())
            self.assertEqual(len(os.listdir(mixin.storage.path)), 0)

    def test_transmission_401(self):
        mixin = TransportMixin()
        mixin.options = Options()
        with LocalFileStorage(os.path.join(TEST_FOLDER, self.id())) as stor:
            mixin.storage = stor
            mixin.storage.put([1, 2, 3])
            with mock.patch('requests.post') as post:
                post.return_value = MockResponse(401, '{}')
                mixin._transmit_from_storage()
            self.assertEqual(len(os.listdir(mixin.storage.path)), 1)

    def test_transmission_500(self):
        mixin = TransportMixin()
        mixin.options = Options()
        with LocalFileStorage(os.path.join(TEST_FOLDER, self.id())) as stor:
            mixin.storage = stor
            mixin.storage.put([1, 2, 3])
            with mock.patch('requests.post') as post:
                post.return_value = MockResponse(500, '{}')
                mixin._transmit_from_storage()
            self.assertIsNone(mixin.storage.get())
            self.assertEqual(len(os.listdir(mixin.storage.path)), 1)

    def test_transmission_400(self):
        mixin = TransportMixin()
        mixin.options = Options()
        with LocalFileStorage(os.path.join(TEST_FOLDER, self.id())) as stor:
            mixin.storage = stor
            mixin.storage.put([1, 2, 3])
            with mock.patch('requests.post') as post:
                post.return_value = MockResponse(400, '{}')
                mixin._transmit_from_storage()
            self.assertEqual(len(os.listdir(mixin.storage.path)), 0)
