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

from opencensus.tags import Tag, TagKey, TagValue
from opencensus.tags.propagation import binary_serializer


class TestBinarySerializer(unittest.TestCase):
    def test_from_byte_array_input_empty(self):
        binary = bytearray(b'')
        propagator = binary_serializer.BinarySerializer()
        tag_context = propagator.from_byte_array(binary=binary)
        expected_tags = {}

        self.assertEqual(expected_tags, tag_context.map)

    def test_from_byte_array_invalid_version_id(self):
        binary = bytearray(b'\x04key1\x04val1')
        propagator = binary_serializer.BinarySerializer()
        with self.assertRaises(ValueError):
            propagator.from_byte_array(binary=binary)

    def test_from_byte_array(self):
        binary = bytearray(b'\x00\x00\x04key1\x04val1\x00\x04key2\x04val2'
                           b'\x00\x04key3\x04val3')
        propagator = binary_serializer.BinarySerializer()
        tag_context = propagator.from_byte_array(binary=binary)
        expected_tags = {'key1': 'val1', 'key2': 'val2', 'key3': 'val3'}

        self.assertEqual(expected_tags, tag_context.map)

    def test_to_byte_array(self):
        from opencensus.tags.tag_map import TagMap

        tags = [Tag(TagKey('key1'), TagValue('val1')),
                Tag(TagKey('key2'), TagValue('val2')),
                Tag(TagKey('key3'), TagValue('val3')),
                Tag(TagKey('key4'), TagValue('val4'))]
        tag_context = TagMap(tags=tags)
        propagator = binary_serializer.BinarySerializer()
        binary = propagator.to_byte_array(tag_context)

        expected_binary = b'\x00\x00\x04key1\x04val1\x00\x04key2\x04val2\x00' \
                          b'\x04key3\x04val3\x00\x04key4\x04val4'

        self.assertEqual(binary, expected_binary)

    def test__parse_tags_invalid_field_id(self):
        from collections import OrderedDict

        propagator = binary_serializer.BinarySerializer()
        binary = bytearray(b'\x00\x00\x04key1\x04val1\x04key2\x04val2'
                           b'\x00\x04key3\x04val3')
        buffer = memoryview(binary)
        tag_context = propagator._parse_tags(buffer)
        expected_dict = OrderedDict(
            [('key1', 'val1')])

        self.assertEqual(frozenset(tag_context.map), frozenset(expected_dict))
