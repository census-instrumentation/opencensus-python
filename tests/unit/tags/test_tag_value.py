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
from opencensus.tags import TagValue


class TestTagValue(unittest.TestCase):
    def test_constructor(self):
        tag_value = TagValue('value')

        self.assertIsNotNone(tag_value)
        self.assertEqual(tag_value, 'value')

    def test_check_value(self):
        test_val1 = 'e9nnb1ixRnvzBH1TUonCG5IsV3ba2PMKjAbSxdLFFpgxFKhZHfi92ajNH6EARaK9FGGShk2EeZ4XObwqIPBwi7j4ZSRR1ZWXtS15keA1h4c9CxeAdakcxxUN0YH6mLJ0BygwRbdbMSeOIPWLo7iyGCil4njKOxH6HF7k0aN4BQl03HQZoXe0t0gd5xKQW37ePNA4FRVZlbLbib3GCF7BeKeA0DKMtuRu27r2hDGEFAmvqh3JEnqOy4gDbhFubaLblr4R4GOHo'  # noqa
        self.assertRaises(ValueError, TagValue, test_val1)

        tag_val2 = TagValue('testVal')
        self.assertIsNotNone(tag_val2)

        test_val3 = 'Æ!01kr'
        self.assertRaises(ValueError, TagValue, test_val3)
