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
from opencensus.tags.tag_key import TagKey


class TestTagKey(unittest.TestCase):

    def test_constructor(self):
        key = 'key1'
        tag_key = TagKey(key)

        self.assertEqual(tag_key.name, key)

    def test_is_valid(self):
        self.assertRaises(ValueError, TagKey, '')

        tag_key1 = TagKey('testKey')
        self.assertTrue(TagKey.is_valid_name(tag_key1.name))

        key3_string = 'e9nnb1ixRnvzBH1TUonCG5IsV3ba2PMKjAbSxdLFFpgxFKhZHfi92ajNH6EARaK9FGGShk2EeZ4XObwqIPBwi7j4ZSRR1ZWXtS15keA1h4c9CxeAdakcxxUN0YH6mLJ0BygwRbdbMSeOIPWLo7iyGCil4njKOxH6HF7k0aN4BQl03HQZoXe0t0gd5xKQW37ePNA4FRVZlbLbib3GCF7BeKeA0DKMtuRu27r2hDGEFAmvqh3JEnqOy4gDbhFubaLblr4R4GOHo'
        self.assertRaises(ValueError, TagKey, key3_string)

        key4_string = 'Æ!01kr'
        self.assertRaises(ValueError, TagKey, key4_string)

        tag_key5 = TagKey(chr(32) + chr(126))
        self.assertTrue(TagKey.is_valid_name(tag_key5.name))

    def test_update_name(self):
        tag_key1 = TagKey('key1')
        tag_key1.name = 'key2'
        self.assertEqual(tag_key1.name, 'key2')

        with self.assertRaises(ValueError):
            tag_key1.name = 'Æ!01kr'
