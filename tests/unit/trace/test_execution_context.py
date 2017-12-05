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

from opencensus.trace import execution_context


class Test__get_opencensus_attr(unittest.TestCase):

    def tearDown(self):
        execution_context.clear()

    def test_no_attrs(self):
        key = 'key'

        result = execution_context.get_opencensus_attr(key)

        self.assertIsNone(result)

    def test_has_attrs(self):
        key = 'key'
        value = 'value'

        execution_context.set_opencensus_attr(key, value)

        result = execution_context.get_opencensus_attr(key)

        self.assertEqual(result, value)
