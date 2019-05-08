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
from opencensus.tags import Tag


class TestTag(unittest.TestCase):

    def test_constructor(self):
        key = 'key1'
        value = 'value1'
        tag = Tag(key=key, value=value)

        self.assertEqual(tag.key, key)
        self.assertEqual(tag.value, value)
        self.assertRaises(ValueError, lambda: Tag(key='', value=value))
        self.assertRaises(ValueError, lambda: Tag(key=key, value='\0'))
