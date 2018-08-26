# -*- coding: utf-8 -*-

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

from opencensus.tags import *


class TestTagMap(unittest.TestCase):

    def test_constructor_defaults(self):
        tag_map = TagMap()
        self.assertEqual(tag_map.map, {})

    def test_constructor_explicit(self):
        tags_list = [Tag(TagKey('key1'), TagValue('value1')),
                     Tag(TagKey('key2'), TagValue('value2'))]
        tag_map = TagMap(tags=tags_list)
        self.assertEqual(tag_map.map, dict(tags_list))

    def test_insert(self):
        test_key = TagKey('key1')
        test_value = TagValue('value1')

        tag_map = TagMap()
        tag_map.insert(key=test_key, value=test_value)
        self.assertEqual({test_key: test_value}, tag_map.map)

        tag_map.insert(key=test_key, value=test_value)
        self.assertEqual({test_key: test_value}, tag_map.map)

        self.assertRaises(ValueError, tag_map.insert, key='Æ!01kr', value=test_value)

    def test_delete(self):
        key = TagKey('key1')
        tag1 = Tag(TagKey('key1'), TagValue('value1'))
        tag2 = Tag(TagKey('key2'), TagValue('value2'))
        tags = [tag1, tag2]

        tag_map = TagMap(tags=tags)
        tag_map.delete(key=key)
        self.assertEqual(tag_map.map, {tag2.key: tag2.value})

    def test_update(self):
        key_1 = TagKey('key1')
        val1 = TagValue('value1')
        tag = Tag(key_1, val1)
        tag_map = TagMap([tag])

        tag_map.update(key=key_1, value=val1)
        self.assertEqual({'key1': 'value1'}, tag_map.map)

        key_2 = TagKey('key2')
        tag_map.update(key=key_2, value=val1)
        self.assertEqual({'key1': 'value1'}, tag_map.map)

        val_2 = TagValue('value2')
        tag_map.update(key=key_1, value=val_2)
        self.assertEqual({'key1': 'value2'}, tag_map.map)

    def test_tag_key_exists(self):
        key = TagKey('key1')
        value = TagValue('val1')
        tag_map = TagMap(tags=[Tag(key, value)])

        self.assertTrue(tag_map.tag_key_exists(key))
        self.assertFalse(tag_map.tag_key_exists('nokey'))

    def test_value(self):
        key = 'key1'
        value = 'value1'
        tag_map = TagMap(tags=[Tag(key, value)])
        test_val = tag_map.get_value(key)
        self.assertEqual(test_val, value)

        with self.assertRaises(KeyError):
            tag_map.get_value(key='not_in_map')
