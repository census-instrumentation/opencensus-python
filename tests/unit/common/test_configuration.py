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

import unittest

from opencensus.common import configuration


class TestConfiguration(unittest.TestCase):
    def test_load_import_error(self):
        with self.assertRaises(ImportError):
            configuration.load('opencensus.nonexist.foo()')

    def test_load_name_error(self):
        with self.assertRaises(NameError):
            configuration.load('nonexist.foo()')

    def test_load_syntax_error(self):
        with self.assertRaises(SyntaxError):
            configuration.load(')')

    def test_load(self):
        ns = configuration.load(
            'opencensus.common.configuration.Namespace("foo")'
        )
        self.assertEqual(ns.name, 'foo')
