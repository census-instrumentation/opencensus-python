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

from opencensus.tags import TagKey


class TestTagKey(unittest.TestCase):
    def test_constructor(self):
        key = 'key1'
        tag_key = TagKey(key)

        self.assertIsNotNone(tag_key)
        self.assertEqual(tag_key, key)

    def test_is_valid(self):
        self.assertRaises(ValueError, TagKey, '')

        tag_key = TagKey('testKey')
        self.assertIsNotNone(tag_key)

        long_name = 'e9nnb1ixRnvzBH1TUonCG5IsV3ba2PMKjAbSxdLFFpgxFKhZHfi92ajNH6EARaK9FGGShk2EeZ4XObwqIPBwi7j4ZSRR1ZWXtS15keA1h4c9CxeAdakcxxUN0YH6mLJ0BygwRbdbMSeOIPWLo7iyGCil4njKOxH6HF7k0aN4BQl03HQZoXe0t0gd5xKQW37ePNA4FRVZlbLbib3GCF7BeKeA0DKMtuRu27r2hDGEFAmvqh3JEnqOy4gDbhFubaLblr4R4GOHo'  # noqa
        self.assertRaises(ValueError, TagKey, long_name)

        invalid_chars_name = 'Æ!01kr'
        self.assertRaises(ValueError, TagKey, invalid_chars_name)

    def test_inclusive_chars(self):
        TagKey(chr(32) + chr(126))
