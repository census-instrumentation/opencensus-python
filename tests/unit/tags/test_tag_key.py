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
from opencensus.tags import tag_key as tag_key_module

class TestTagKey(unittest.TestCase):

    def test_constructor(self):
        key = 'key1'
        tag_key = tag_key_module.TagKey(key)

        self.assertEqual(tag_key.name, key)

    def test_is_valid(self):
        test_key3 = 'e9nnb1ixRnvzBH1TUonCG5IsV3ba2PMKjAbSxdLFFpgxFKhZHfi92ajNH6EARaK9FGGShk2EeZ4XObwqIPBwi7j4ZSRR1ZWXtS15keA1h4c9CxeAdakcxxUN0YH6mLJ0BygwRbdbMSeOIPWLo7iyGCil4njKOxH6HF7k0aN4BQl03HQZoXe0t0gd5xKQW37ePNA4FRVZlbLbib3GCF7BeKeA0DKMtuRu27r2hDGEFAmvqh3JEnqOy4gDbhFubaLblr4R4GOHo'
        tag_key1 = tag_key_module.TagKey('')
        self.assertFalse(tag_key1.check_name(tag_key1.name))
        tag_key2 = tag_key_module.TagKey('testKey')
        self.assertTrue(tag_key2.check_name(tag_key2.name))
        tag_key3 = tag_key_module.TagKey(test_key3)
        self.assertFalse(tag_key3.check_name(tag_key3.name))
