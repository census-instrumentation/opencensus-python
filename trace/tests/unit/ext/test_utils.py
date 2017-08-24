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

from opencensus.trace.ext import utils


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
