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
