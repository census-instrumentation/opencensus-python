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
import mock
from opencensus.tags import tag_map as tag_map_module

class TestTagMap(unittest.TestCase):

    def test_constructor_defaults(self):
        tag_map = tag_map_module.TagMap()
        self.assertEqual(tag_map.tags, {})
        self.assertEqual(tag_map.map, {})

    def test_constructor_explicit(self):
        tags = [{'key1': 'value1'}]
        map = {}

        tag_map = tag_map_module.TagMap(tags=tags, map=map)
        self.assertEqual(tag_map.tags, tags)
        self.assertEqual(tag_map.map, map)

    def test_insert(self):
        test_key = 'key1'
        test_value = 'value1'
        tag_map = tag_map_module.TagMap()
        tag_map.insert(key=test_key, value=test_value)
        self.assertEqual({'key1': 'value1'}, tag_map.map)

    def test_delete(self):
        key = 'key1'
        tag_map = tag_map_module.TagMap(tags=[{'key1': 'value1', 'key2': 'value2'}])
        tag_map.delete('key1')
        self.assertEqual(tag_map.map, {'key2': 'value2'})

    def test_update(self):
        key = 'key1'
        value = 'value1'
        tag_map = tag_map_module.TagMap(tags=[{'key1': 'value2'}])
        tag_map.update(key=key, value=value)
        self.assertEqual({'key1': 'value1'}, tag_map.map)

    def test_tag_key_exists(self):
        key = mock.Mock()
        value = mock.Mock()
        tag_map = tag_map_module.TagMap(tags=[{key: value}])
        self.assertTrue(tag_map.tag_key_exists(key))
        self.assertFalse(tag_map.tag_key_exists('nokey'))

    def test_value(self):
        key = 'key1'
        value = 'value1'
        tag_map = tag_map_module.TagMap(tags=[{key: value}])
        test_val = tag_map.get_value(key)
        self.assertEqual(test_val, value)
