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
from opencensus.ext.azure.common.transport import (
    _MAX_CONSECUTIVE_REDIRECTS,
    _MONITOR_OAUTH_SCOPE,
    _REACHED_INGESTION_STATUS_CODES,
    TransportMixin,
    TransportStatusCode,
    _requests_map,
)
from opencensus.ext.azure.statsbeat import state

TEST_FOLDER = os.path.abspath('.test.transport')


def setUpModule():
    os.makedirs(TEST_FOLDER)


def tearDownModule():
    shutil.rmtree(TEST_FOLDER)


def throw(exc_type, *args, **kwargs):
    def func(*_args, **_kwargs):
        raise exc_type(*args, **kwargs)
    return func


class MockResponse(object):
    def __init__(self, status_code, text, headers=None):
        self.status_code = status_code
        self.text = text
        self.headers = headers


# pylint: disable=W0212
class TestTransportMixin(unittest.TestCase):
    def setUp(self):
        # pylint: disable=protected-access
        _requests_map.clear()
        state._STATSBEAT_STATE = {
            "INITIAL_FAILURE_COUNT": 0,
            "INITIAL_SUCCESS": False,
            "SHUTDOWN": False,
        }

    def test_check_stats_collection(self):
        mixin = TransportMixin()
        with mock.patch.dict(
                os.environ, {
                    "APPLICATIONINSIGHTS_STATSBEAT_DISABLED_ALL": "",
                }):
            self.assertTrue(mixin._check_stats_collection())
        with mock.patch.dict(
                os.environ, {
                    "APPLICATIONINSIGHTS_STATSBEAT_DISABLED_ALL": "True",
                }):
            self.assertFalse(mixin._check_stats_collection())
        mixin._is_stats = False
        self.assertTrue(mixin._check_stats_collection())
        mixin._is_stats = True
        self.assertFalse(mixin._check_stats_collection())
        mixin._is_stats = False
        state._STATSBEAT_STATE["SHUTDOWN"] = False
        self.assertTrue(mixin._check_stats_collection())
        state._STATSBEAT_STATE["SHUTDOWN"] = True
        self.assertFalse(mixin._check_stats_collection())

    def test_initial_statsbeat_success(self):
        self.assertFalse(state._STATSBEAT_STATE["INITIAL_SUCCESS"])
        mixin = TransportMixin()
        mixin.options = Options()
        mixin._is_stats = True
        with mock.patch('requests.post') as post:
            for code in _REACHED_INGESTION_STATUS_CODES:
                post.return_value = MockResponse(code, 'unknown')
                mixin._transmit([1])
                self.assertTrue(state._STATSBEAT_STATE["INITIAL_SUCCESS"])
                state._STATSBEAT_STATE["INITIAL_SUCCESS"] = False

    def test_exception_statsbeat_shutdown_increment(self):
        mixin = TransportMixin()
        mixin.options = Options()
        mixin._is_stats = True
        state._STATSBEAT_STATE["INITIAL_SUCCESS"] = False
        state._STATSBEAT_STATE["INITIAL_FAILURE_COUNT"] = 0
        state._STATSBEAT_STATE["SHUTDOWN"] = False
        with mock.patch.dict(
                os.environ, {
                    "APPLICATIONINSIGHTS_STATSBEAT_DISABLED_ALL": "",
                }):
            with mock.patch('requests.post', throw(Exception)):
                result = mixin._transmit([1, 2, 3])
                self.assertEqual(state._STATSBEAT_STATE["INITIAL_FAILURE_COUNT"], 1)  # noqa: E501
                self.assertEqual(result, TransportStatusCode.DROP)

    def test_exception_statsbeat_shutdown(self):
        mixin = TransportMixin()
        mixin.options = Options()
        mixin._is_stats = True
        state._STATSBEAT_STATE["INITIAL_SUCCESS"] = False
        state._STATSBEAT_STATE["INITIAL_FAILURE_COUNT"] = 2
        state._STATSBEAT_STATE["SHUTDOWN"] = False
        with mock.patch.dict(
                os.environ, {
                    "APPLICATIONINSIGHTS_STATSBEAT_DISABLED_ALL": "",
                }):
            with mock.patch('requests.post', throw(Exception)):
                result = mixin._transmit([1, 2, 3])
                self.assertEqual(state._STATSBEAT_STATE["INITIAL_FAILURE_COUNT"], 3)  # noqa: E501
                self.assertEqual(result, TransportStatusCode.STATSBEAT_SHUTDOWN)  # noqa: E501

    def test_status_code_statsbeat_shutdown_increment(self):
        mixin = TransportMixin()
        mixin.options = Options()
        mixin._is_stats = True
        state._STATSBEAT_STATE["INITIAL_SUCCESS"] = False
        state._STATSBEAT_STATE["INITIAL_FAILURE_COUNT"] = 0
        state._STATSBEAT_STATE["SHUTDOWN"] = False
        with mock.patch.dict(
                os.environ, {
                    "APPLICATIONINSIGHTS_STATSBEAT_DISABLED_ALL": "",
                }):
            with mock.patch('requests.post') as post:
                post.return_value = MockResponse(403, 'unknown')
                mixin._transmit([1, 2, 3])
                self.assertEqual(state._STATSBEAT_STATE["INITIAL_FAILURE_COUNT"], 1)  # noqa: E501
                self.assertFalse(state._STATSBEAT_STATE["INITIAL_SUCCESS"])
            with mock.patch('requests.post') as post:
                post.return_value = MockResponse(200, 'unknown')
                mixin._transmit([1, 2, 3])
                self.assertEqual(state._STATSBEAT_STATE["INITIAL_FAILURE_COUNT"], 1)  # noqa: E501
                self.assertTrue(state._STATSBEAT_STATE["INITIAL_SUCCESS"])

    def test_status_code_statsbeat_shutdown(self):
        mixin = TransportMixin()
        mixin.options = Options()
        mixin._is_stats = True
        state._STATSBEAT_STATE["INITIAL_SUCCESS"] = False
        state._STATSBEAT_STATE["INITIAL_FAILURE_COUNT"] = 2
        state._STATSBEAT_STATE["SHUTDOWN"] = False
        with mock.patch.dict(
                os.environ, {
                    "APPLICATIONINSIGHTS_STATSBEAT_DISABLED_ALL": "",
                }):
            with mock.patch('requests.post') as post:
                post.return_value = MockResponse(403, 'unknown')
                result = mixin._transmit([1, 2, 3])
                self.assertEqual(state._STATSBEAT_STATE["INITIAL_FAILURE_COUNT"], 3)  # noqa: E501
                self.assertFalse(state._STATSBEAT_STATE["INITIAL_SUCCESS"])
                self.assertEqual(result, TransportStatusCode.STATSBEAT_SHUTDOWN)  # noqa: E501

    def test_transmission_nothing(self):
        mixin = TransportMixin()
        with LocalFileStorage(os.path.join(TEST_FOLDER, self.id())) as stor:
            mixin.storage = stor
            with mock.patch('requests.post') as post:
                post.return_value = None
                mixin._transmit_from_storage()

    def test_transmission_timeout(self):
        mixin = TransportMixin()
        mixin.options = Options()
        with LocalFileStorage(os.path.join(TEST_FOLDER, self.id())) as stor:
            mixin.storage = stor
            mixin.storage.put([1, 2, 3])
            with mock.patch('requests.post', throw(requests.Timeout)):
                mixin._transmit_from_storage()
            self.assertIsNone(mixin.storage.get())
            self.assertEqual(len(os.listdir(mixin.storage.path)), 1)

    def test_statsbeat_timeout(self):
        mixin = TransportMixin()
        mixin.options = Options()
        with mock.patch('requests.post', throw(requests.Timeout)):
            result = mixin._transmit([1, 2, 3])
            self.assertEqual(len(_requests_map), 3)
            self.assertIsNotNone(_requests_map['duration'])
            self.assertEqual(_requests_map['count'], 1)
            self.assertEqual(_requests_map['exception']['Timeout'], 1)
            self.assertEqual(result, TransportStatusCode.RETRY)

    def test_transmission_req_exception(self):
        mixin = TransportMixin()
        mixin.options = Options()
        with LocalFileStorage(os.path.join(TEST_FOLDER, self.id())) as stor:
            mixin.storage = stor
            mixin.storage.put([1, 2, 3])
            with mock.patch('requests.post', throw(requests.RequestException)):
                mixin._transmit_from_storage()
            self.assertIsNone(mixin.storage.get())
            self.assertEqual(len(os.listdir(mixin.storage.path)), 1)

    def test_statsbeat_req_exception(self):
        mixin = TransportMixin()
        mixin.options = Options()
        with mock.patch('requests.post', throw(requests.RequestException)):
            result = mixin._transmit([1, 2, 3])
            self.assertEqual(len(_requests_map), 3)
            self.assertIsNotNone(_requests_map['duration'])
            self.assertEqual(_requests_map['count'], 1)
            self.assertEqual(_requests_map['exception']['RequestException'], 1)
            self.assertEqual(result, TransportStatusCode.RETRY)

    def test_transmission_cred_exception(self):
        mixin = TransportMixin()
        mixin.options = Options()
        with LocalFileStorage(os.path.join(TEST_FOLDER, self.id())) as stor:
            mixin.storage = stor
            mixin.storage.put([1, 2, 3])
            with mock.patch('requests.post', throw(CredentialUnavailableError)):  # noqa: E501
                mixin._transmit_from_storage()
            self.assertIsNone(mixin.storage.get())
            self.assertEqual(len(os.listdir(mixin.storage.path)), 0)

    def test_statsbeat_cred_exception(self):
        mixin = TransportMixin()
        mixin.options = Options()
        with mock.patch('requests.post', throw(CredentialUnavailableError)):
            result = mixin._transmit([1, 2, 3])
            self.assertEqual(len(_requests_map), 3)
            self.assertIsNotNone(_requests_map['duration'])
            self.assertEqual(_requests_map['exception']['CredentialUnavailableError'], 1)  # noqa: E501
            self.assertEqual(_requests_map['count'], 1)
            self.assertEqual(result, TransportStatusCode.DROP)

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

    def test_statsbeat_client_exception(self):
        mixin = TransportMixin()
        mixin.options = Options()
        with mock.patch('requests.post', throw(ClientAuthenticationError)):
            result = mixin._transmit([1, 2, 3])
            self.assertEqual(len(_requests_map), 3)
            self.assertIsNotNone(_requests_map['duration'])
            self.assertEqual(_requests_map['exception']['ClientAuthenticationError'], 1)  # noqa: E501
            self.assertEqual(_requests_map['count'], 1)
            self.assertEqual(result, TransportStatusCode.RETRY)

    def test_transmission_exception(self):
        mixin = TransportMixin()
        mixin.options = Options()
        with LocalFileStorage(os.path.join(TEST_FOLDER, self.id())) as stor:
            mixin.storage = stor
            mixin.storage.put([1, 2, 3])
            with mock.patch('requests.post', throw(Exception)):
                mixin._transmit_from_storage()
            self.assertIsNone(mixin.storage.get())
            self.assertEqual(len(os.listdir(mixin.storage.path)), 0)

    def test_statsbeat_exception(self):
        mixin = TransportMixin()
        mixin.options = Options()
        with mock.patch('requests.post', throw(Exception)):
            result = mixin._transmit([1, 2, 3])
            self.assertEqual(len(_requests_map), 3)
            self.assertIsNotNone(_requests_map['duration'])
            self.assertEqual(_requests_map['exception']['Exception'], 1)
            self.assertEqual(_requests_map['count'], 1)
            self.assertEqual(result, TransportStatusCode.DROP)

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

    def test_transmission_text_exception(self):
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

    def test_statsbeat_200(self):
        mixin = TransportMixin()
        mixin.options = Options()
        with mock.patch('requests.post') as post:
            post.return_value = MockResponse(200, 'unknown')
            result = mixin._transmit([1, 2, 3])
            self.assertEqual(len(_requests_map), 3)
            self.assertIsNotNone(_requests_map['duration'])
            self.assertEqual(_requests_map['success'], 1)
            self.assertEqual(_requests_map['count'], 1)
            self.assertEqual(result, TransportStatusCode.SUCCESS)

    def test_transmission_auth(self):
        mixin = TransportMixin()
        mixin.options = Options()
        url = 'https://dc.services.visualstudio.com'
        mixin.options.endpoint = url
        credential = mock.Mock()
        mixin.options.credential = credential
        token_mock = mock.Mock()
        token_mock.token = "test_token"
        credential.get_token.return_value = token_mock
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
                    url=url + '/v2.1/track',
                    data=data,
                    headers=headers,
                    timeout=10.0,
                    proxies={},
                    allow_redirects=False,
                )
            credential.get_token.assert_called_with(_MONITOR_OAUTH_SCOPE)
            self.assertIsNone(mixin.storage.get())
            self.assertEqual(len(os.listdir(mixin.storage.path)), 0)
            credential.get_token.assert_called_once()

    def test_transmission_206_invalid_data(self):
        mixin = TransportMixin()
        mixin.options = Options()
        with LocalFileStorage(os.path.join(TEST_FOLDER, self.id())) as stor:
            mixin.storage = stor
            mixin.storage.put([1, 2, 3])
            with mock.patch('requests.post') as post:
                post.return_value = MockResponse(206, 'unknown')
                mixin._transmit_from_storage()
            self.assertIsNone(mixin.storage.get())
            self.assertEqual(len(os.listdir(mixin.storage.path)), 0)

    def test_statsbeat_206_invalid_data(self):
        mixin = TransportMixin()
        mixin.options = Options()
        with mock.patch('requests.post') as post:
            post.return_value = MockResponse(206, 'unknown')
            result = mixin._transmit([1, 2, 3])
            self.assertEqual(len(_requests_map), 3)
            self.assertIsNotNone(_requests_map['duration'])
            self.assertEqual(_requests_map['count'], 1)
            self.assertEqual(result, TransportStatusCode.DROP)

    def test_transmission_206_partial_retry(self):
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
                            'statusCode': 400,  # dropped
                            'message': '',
                        },
                        {
                            'index': 2,
                            'statusCode': 500,  # retry
                            'message': 'Internal Server Error',
                        },
                    ],
                }))
                mixin._transmit_from_storage()
            self.assertEqual(len(os.listdir(mixin.storage.path)), 1)
            self.assertEqual(mixin.storage.get().get(), (3,))

    def test_statsbeat_206_partial_retry(self):
        mixin = TransportMixin()
        mixin.options = Options()
        storage_mock = mock.Mock()
        mixin.storage = storage_mock
        with mock.patch('requests.post') as post:
            post.return_value = MockResponse(206, json.dumps({
                    'itemsReceived': 5,
                    'itemsAccepted': 3,
                    'errors': [
                        {
                            'index': 0,
                            'statusCode': 400,  # dropped
                            'message': '',
                        },
                        {
                            'index': 2,
                            'statusCode': 500,  # retry
                            'message': 'Internal Server Error',
                        },
                    ],
                }))
            result = mixin._transmit([1, 2, 3])
            # We do not record any network statsbeat for 206 status code
            self.assertEqual(len(_requests_map), 2)
            self.assertIsNotNone(_requests_map['duration'])
            self.assertIsNone(_requests_map.get('retry'))
            self.assertEqual(_requests_map['count'], 1)
            self.assertEqual(result, TransportStatusCode.DROP)
            storage_mock.put.assert_called_once()

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
                            'statusCode': 400,  # dropped
                            'message': '',
                        },
                    ],
                }))
                mixin._transmit_from_storage()
            self.assertEqual(len(os.listdir(mixin.storage.path)), 0)

    def test_statsbeat_206_no_retry(self):
        mixin = TransportMixin()
        mixin.options = Options()
        storage_mock = mock.Mock()
        mixin.storage = storage_mock
        with mock.patch('requests.post') as post:
            post.return_value = MockResponse(206, json.dumps({
                    'itemsReceived': 3,
                    'itemsAccepted': 2,
                    'errors': [
                        {
                            'index': 0,
                            'statusCode': 400,  # dropped
                            'message': '',
                        },
                    ],
                }))
            result = mixin._transmit([1, 2, 3])
            self.assertEqual(len(_requests_map), 2)
            self.assertIsNotNone(_requests_map['duration'])
            self.assertEqual(_requests_map['count'], 1)
            self.assertEqual(result, TransportStatusCode.DROP)
            storage_mock.put.assert_not_called()

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

    def test_statsbeat_206_bogus(self):
        mixin = TransportMixin()
        mixin.options = Options()
        storage_mock = mock.Mock()
        mixin.storage = storage_mock
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
            result = mixin._transmit([1, 2, 3])
            self.assertEqual(len(_requests_map), 3)
            self.assertIsNotNone(_requests_map['duration'])
            self.assertEqual(_requests_map['count'], 1)
            self.assertEqual(_requests_map['exception']['KeyError'], 1)
            self.assertEqual(result, TransportStatusCode.DROP)
            storage_mock.put.assert_not_called()

    def test_transmission_429(self):
        mixin = TransportMixin()
        mixin.options = Options()
        with LocalFileStorage(os.path.join(TEST_FOLDER, self.id())) as stor:
            mixin.storage = stor
            mixin.storage.put([1, 2, 3])
            with mock.patch('requests.post') as post:
                post.return_value = MockResponse(429, 'unknown')
                mixin._transmit_from_storage()
            self.assertIsNone(mixin.storage.get())
            self.assertEqual(len(os.listdir(mixin.storage.path)), 1)

    def test_statsbeat_429(self):
        mixin = TransportMixin()
        mixin.options = Options()
        with mock.patch('requests.post') as post:
            post.return_value = MockResponse(429, 'unknown')
            result = mixin._transmit([1, 2, 3])
            self.assertEqual(len(_requests_map), 3)
            self.assertIsNotNone(_requests_map['duration'])
            self.assertEqual(_requests_map['retry'][429], 1)
            self.assertEqual(_requests_map['count'], 1)
            self.assertEqual(result, TransportStatusCode.RETRY)

    def test_transmission_500(self):
        mixin = TransportMixin()
        mixin.options = Options()
        with LocalFileStorage(os.path.join(TEST_FOLDER, self.id())) as stor:
            mixin.storage = stor
            mixin.storage.put([1, 2, 3])
            with mock.patch('requests.post') as post:
                post.return_value = MockResponse(500, 'unknown')
                mixin._transmit_from_storage()
            self.assertIsNone(mixin.storage.get())
            self.assertEqual(len(os.listdir(mixin.storage.path)), 1)

    def test_statsbeat_500(self):
        mixin = TransportMixin()
        mixin.options = Options()
        with mock.patch('requests.post') as post:
            post.return_value = MockResponse(500, 'unknown')
            result = mixin._transmit([1, 2, 3])
            self.assertEqual(len(_requests_map), 3)
            self.assertIsNotNone(_requests_map['duration'])
            self.assertEqual(_requests_map['retry'][500], 1)
            self.assertEqual(_requests_map['count'], 1)
            self.assertEqual(result, TransportStatusCode.RETRY)

    def test_transmission_502(self):
        mixin = TransportMixin()
        mixin.options = Options()
        with LocalFileStorage(os.path.join(TEST_FOLDER, self.id())) as stor:
            mixin.storage = stor
            mixin.storage.put([1, 2, 3])
            with mock.patch('requests.post') as post:
                post.return_value = MockResponse(502, 'unknown')
                mixin._transmit_from_storage()
            self.assertIsNone(mixin.storage.get())
            self.assertEqual(len(os.listdir(mixin.storage.path)), 1)

    def test_statsbeat_502(self):
        mixin = TransportMixin()
        mixin.options = Options()
        with mock.patch('requests.post') as post:
            post.return_value = MockResponse(502, 'unknown')
            result = mixin._transmit([1, 2, 3])
            self.assertEqual(len(_requests_map), 3)
            self.assertIsNotNone(_requests_map['duration'])
            self.assertEqual(_requests_map['retry'][502], 1)
            self.assertEqual(_requests_map['count'], 1)
            self.assertEqual(result, TransportStatusCode.RETRY)

    def test_transmission_503(self):
        mixin = TransportMixin()
        mixin.options = Options()
        with LocalFileStorage(os.path.join(TEST_FOLDER, self.id())) as stor:
            mixin.storage = stor
            mixin.storage.put([1, 2, 3])
            with mock.patch('requests.post') as post:
                post.return_value = MockResponse(503, 'unknown')
                mixin._transmit_from_storage()
            self.assertIsNone(mixin.storage.get())
            self.assertEqual(len(os.listdir(mixin.storage.path)), 1)

    def test_statsbeat_503(self):
        mixin = TransportMixin()
        mixin.options = Options()
        with mock.patch('requests.post') as post:
            post.return_value = MockResponse(503, 'unknown')
            result = mixin._transmit([1, 2, 3])
            self.assertEqual(len(_requests_map), 3)
            self.assertIsNotNone(_requests_map['duration'])
            self.assertEqual(_requests_map['retry'][503], 1)
            self.assertEqual(_requests_map['count'], 1)
            self.assertEqual(result, TransportStatusCode.RETRY)

    def test_transmission_504(self):
        mixin = TransportMixin()
        mixin.options = Options()
        with LocalFileStorage(os.path.join(TEST_FOLDER, self.id())) as stor:
            mixin.storage = stor
            mixin.storage.put([1, 2, 3])
            with mock.patch('requests.post') as post:
                post.return_value = MockResponse(504, 'unknown')
                mixin._transmit_from_storage()
            self.assertIsNone(mixin.storage.get())
            self.assertEqual(len(os.listdir(mixin.storage.path)), 1)

    def test_statsbeat_504(self):
        mixin = TransportMixin()
        mixin.options = Options()
        with mock.patch('requests.post') as post:
            post.return_value = MockResponse(504, 'unknown')
            result = mixin._transmit([1, 2, 3])
            self.assertEqual(len(_requests_map), 3)
            self.assertIsNotNone(_requests_map['duration'])
            self.assertEqual(_requests_map['retry'][504], 1)
            self.assertEqual(_requests_map['count'], 1)
            self.assertEqual(result, TransportStatusCode.RETRY)

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

    def test_statsbeat_401(self):
        mixin = TransportMixin()
        mixin.options = Options()
        with mock.patch('requests.post') as post:
            post.return_value = MockResponse(401, 'unknown')
            result = mixin._transmit([1, 2, 3])
            self.assertEqual(len(_requests_map), 3)
            self.assertIsNotNone(_requests_map['duration'])
            self.assertEqual(_requests_map['retry'][401], 1)
            self.assertEqual(_requests_map['count'], 1)
            self.assertEqual(result, TransportStatusCode.RETRY)

    def test_transmission_403(self):
        mixin = TransportMixin()
        mixin.options = Options()
        with LocalFileStorage(os.path.join(TEST_FOLDER, self.id())) as stor:
            mixin.storage = stor
            mixin.storage.put([1, 2, 3])
            with mock.patch('requests.post') as post:
                post.return_value = MockResponse(403, '{}')
                mixin._transmit_from_storage()
            self.assertEqual(len(os.listdir(mixin.storage.path)), 1)

    def test_statsbeat_403(self):
        mixin = TransportMixin()
        mixin.options = Options()
        with mock.patch('requests.post') as post:
            post.return_value = MockResponse(403, 'unknown')
            result = mixin._transmit([1, 2, 3])
            self.assertEqual(len(_requests_map), 3)
            self.assertIsNotNone(_requests_map['duration'])
            self.assertEqual(_requests_map['retry'][403], 1)
            self.assertEqual(_requests_map['count'], 1)
            self.assertEqual(result, TransportStatusCode.RETRY)

    def test_transmission_307(self):
        mixin = TransportMixin()
        mixin.options = Options()
        mixin._consecutive_redirects = 0
        mixin.options.endpoint = "test.endpoint"
        with LocalFileStorage(os.path.join(TEST_FOLDER, self.id())) as stor:
            mixin.storage = stor
            mixin.storage.put([1, 2, 3])
            with mock.patch('requests.post') as post:
                post.return_value = MockResponse(307, '{}', {"location": "https://example.com"})  # noqa: E501
                mixin._transmit_from_storage()
            self.assertEqual(post.call_count, _MAX_CONSECUTIVE_REDIRECTS)
            self.assertEqual(len(os.listdir(mixin.storage.path)), 0)
            self.assertEqual(mixin.options.endpoint, "https://example.com")

    def test_transmission_307_circular_reference(self):
        mixin = TransportMixin()
        mixin.options = Options()
        mixin._consecutive_redirects = 0
        mixin.options.endpoint = "https://example.com"
        with mock.patch('requests.post') as post:
            post.return_value = MockResponse(307, '{}', {"location": "https://example.com"})  # noqa: E501
            result = mixin._transmit([1, 2, 3])
            self.assertEqual(result, TransportStatusCode.DROP)
        self.assertEqual(post.call_count, _MAX_CONSECUTIVE_REDIRECTS)
        self.assertEqual(mixin.options.endpoint, "https://example.com")

    def test_statsbeat_307(self):
        mixin = TransportMixin()
        mixin.options = Options()
        mixin._consecutive_redirects = 0
        mixin.options.endpoint = "test.endpoint"
        with mock.patch('requests.post') as post:
            post.return_value = MockResponse(307, '{}', {"location": "https://example.com"})  # noqa: E501
            result = mixin._transmit([1, 2, 3])
            self.assertEqual(len(_requests_map), 3)
            self.assertIsNotNone(_requests_map['duration'])
            self.assertEqual(_requests_map['exception']['Circular Redirect'], 1)  # noqa: E501
            self.assertEqual(_requests_map['count'], 10)
            self.assertEqual(result, TransportStatusCode.DROP)

    def test_transmission_439(self):
        mixin = TransportMixin()
        mixin.options = Options()
        with LocalFileStorage(os.path.join(TEST_FOLDER, self.id())) as stor:
            mixin.storage = stor
            mixin.storage.put([1, 2, 3])
            with mock.patch('requests.post') as post:
                post.return_value = MockResponse(439, '{}')
                mixin._transmit_from_storage()
            self.assertEqual(len(os.listdir(mixin.storage.path)), 0)

    def test_statsbeat_439(self):
        mixin = TransportMixin()
        mixin.options = Options()
        with mock.patch('requests.post') as post:
            post.return_value = MockResponse(439, 'unknown')
            result = mixin._transmit([1, 2, 3])
            self.assertEqual(len(_requests_map), 3)
            self.assertIsNotNone(_requests_map['duration'])
            self.assertEqual(_requests_map['throttle'][439], 1)
            self.assertEqual(_requests_map['count'], 1)
            self.assertEqual(result, TransportStatusCode.DROP)
