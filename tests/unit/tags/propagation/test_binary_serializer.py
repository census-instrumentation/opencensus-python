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
from opencensus.tags.propagation import binary_serializer
from opencensus.tags import tag_key
from opencensus.tags import tag_value
from opencensus.tags import tag_map


class TestBinarySerializer(unittest.TestCase):
    def test_from_byte_array(self):
        binary = bytearray(b'\x00\x00\x04key1\x04val1\x00\x04key2\x04val2'
                           b'\x00\x04key3\x04val3')
        propagator = binary_serializer.BinarySerializer()
        tag_context = propagator.from_byte_array(binary=binary)

        expected_tags = [{'key1': 'val1', 'key2': 'val2', 'key3': 'val3'}]

        self.assertEqual(expected_tags, tag_context)

    def test_to_byte_array(self):
        from opencensus.tags.tag_map import TagMap

        tags = [{'key1': 'val1', 'key2': 'val2', 'key3': 'val3', 'key4': 'val4'}]
        tag_context = TagMap(tags=tags)

        propagator = binary_serializer.BinarySerializer()

        binary = propagator.to_byte_array(tag_context)
        exp_tags = propagator.from_byte_array(bytearray(binary))
        print("exp_tgs: ", exp_tags)
        print("binary: ", binary)
        expected_binary = b'\x00\x00\x04key1\x04val1\x00\x04key2\x04val2\x00' \
                          b'\x04key3\x04val3\x00\x04key4\x04val4'
        self.assertTrue(propagator.from_byte_array(bytearray(binary)) ==
                        propagator.from_byte_array(bytearray(expected_binary)))

    def test_parse_tags(self):
            '''finish'''

    def test_encode_tag(self):
        '''finish'''

    def test_encode_string(self):
        '''finish'''

    def test_decode_string(self):
        '''finish'''
