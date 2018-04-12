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
from opencensus.tags import tag_value as tag_value_module

class TestTagValue(unittest.TestCase):

    def test_constructor(self):
        value = 'value1'
        tag_value = tag_value_module.TagValue(value=value)

        self.assertEqual(tag_value.value, value)

    def test_check_value(self):
        test_val1 = 'e9nnb1ixRnvzBH1TUonCG5IsV3ba2PMKjAbSxdLFFpgxFKhZHfi92ajNH6EARaK9FGGShk2EeZ4XObwqIPBwi7j4ZSRR1ZWXtS15keA1h4c9CxeAdakcxxUN0YH6mLJ0BygwRbdbMSeOIPWLo7iyGCil4njKOxH6HF7k0aN4BQl03HQZoXe0t0gd5xKQW37ePNA4FRVZlbLbib3GCF7BeKeA0DKMtuRu27r2hDGEFAmvqh3JEnqOy4gDbhFubaLblr4R4GOHo'
        tag_val1 = tag_value_module.TagValue(test_val1)
        self.assertFalse(tag_val1.check_value(tag_val1.value))

        tag_val2 = tag_value_module.TagValue('testVal')
        self.assertTrue(tag_val2.check_value(tag_val2.value))
