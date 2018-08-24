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

from opencensus.tags import execution_context
from opencensus.tags import tag_key as tag_key_module
from opencensus.tags import tag_map as tag_map_module
from opencensus.tags import tag_value as tag_value_module


class TestTagExecutionContext(unittest.TestCase):

    def tearDown(self):
        execution_context.clear()

    def test_unset_tag_map(self):
        result = execution_context.get_current_tag_map()

        self.assertIsNone(result)

    def test_set_and_get_tag_map(self):
        key = tag_key_module.TagKey('key')
        value = tag_value_module.TagValue('value')
        tag_map = tag_map_module.TagMap()
        tag_map.insert(key, value)

        execution_context.set_current_tag_map(tag_map)

        result = execution_context.get_current_tag_map()

        self.assertEqual(result, tag_map)
