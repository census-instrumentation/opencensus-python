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

from google.rpc import code_pb2
from opencensus.trace import utils


class TestUtils(unittest.TestCase):

    def test_get_func_name(self):
        func = mock.Mock()
        func.__name__ = 'test_func'
        func.__module__ = 'test.module'

        func_name = utils.get_func_name(func)
        expected_func_name = 'test.module.test_func'

        self.assertEqual(func_name, expected_func_name)

    def test_get_func_no_module(self):
        func = mock.Mock()
        func.__name__ = 'test_func'
        func.__module__ = None

        func_name = utils.get_func_name(func)
        expected_func_name = 'test_func'

        self.assertEqual(func_name, expected_func_name)

    def test_disable_tracing_url_default(self):
        url = 'http://127.0.0.1:8080/_ah/health'
        disable_tracing = utils.disable_tracing_url(url)
        self.assertTrue(disable_tracing)

        url = 'http://127.0.0.1:8080/mysql'
        disable_tracing = utils.disable_tracing_url(url)
        self.assertFalse(disable_tracing)

    def test_disable_tracing_url_explicit(self):
        url = 'http://127.0.0.1:8080/test_no_tracing'
        blacklist_paths = ['test_no_tracing']

        disable_tracing = utils.disable_tracing_url(url, blacklist_paths)
        self.assertTrue(disable_tracing)

    def test_disable_tracing_hostname_default(self):
        url = '127.0.0.1:8080'

        disable_tracing = utils.disable_tracing_hostname(url)
        self.assertFalse(disable_tracing)

    def test_disable_tracing_hostname_explicit(self):
        blacklist_paths = ['127.0.0.1', '192.168.0.1:80']

        url = '127.0.0.1:8080'
        disable_tracing = utils.disable_tracing_hostname(url, blacklist_paths)
        self.assertFalse(disable_tracing)

        url = '127.0.0.1:80'
        disable_tracing = utils.disable_tracing_hostname(url, blacklist_paths)
        self.assertFalse(disable_tracing)

    def test_grpc_code_from_http_code(self):
        test_cases = [
            {
                'http_code': 0,
                'grpc_code': code_pb2.UNKNOWN,
            },
            {
                'http_code': 200,
                'grpc_code': code_pb2.OK,
            },
            {
                'http_code': 399,
                'grpc_code': code_pb2.OK,
            },
            {
                'http_code': 400,
                'grpc_code': code_pb2.INVALID_ARGUMENT,
            },
            {
                'http_code': 504,
                'grpc_code': code_pb2.DEADLINE_EXCEEDED,
            },
            {
                'http_code': 404,
                'grpc_code': code_pb2.NOT_FOUND,
            },
            {
                'http_code': 403,
                'grpc_code': code_pb2.PERMISSION_DENIED,
            },
            {
                'http_code': 401,
                'grpc_code': code_pb2.UNAUTHENTICATED,
            },
            {
                'http_code': 429,
                'grpc_code': code_pb2.RESOURCE_EXHAUSTED,
            },
            {
                'http_code': 501,
                'grpc_code': code_pb2.UNIMPLEMENTED,
            },
            {
                'http_code': 503,
                'grpc_code': code_pb2.UNAVAILABLE,
            },
            {
                'http_code': 600,
                'grpc_code': code_pb2.UNKNOWN,
            },
        ]

        for test_case in test_cases:
            status = utils.status_from_http_code(test_case['http_code'])
            self.assertEqual(
                status.canonical_code,
                test_case['grpc_code'],
                'HTTP: {} / GRPC: expected = {}, actual = {}'.format(
                    test_case['http_code'],
                    test_case['grpc_code'],
                    status.canonical_code,
                )
            )
