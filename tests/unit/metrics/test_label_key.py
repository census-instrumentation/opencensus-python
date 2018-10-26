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
from opencensus.metrics import label_key as label_key_module


class TestLabelKey(unittest.TestCase):

    def test_constructor(self):
        key = 'key1'
        description = 'description1'
        label_key = label_key_module.LabelKey(key, description)

        self.assertIsNotNone(label_key)
        self.assertEqual(label_key.key, key)
        self.assertEqual(label_key.description, description)

    def test_constructor_Empty(self):
        key = ''
        description = ''
        label_key = label_key_module.LabelKey(key, description)

        self.assertIsNotNone(label_key)
        self.assertEqual(label_key.key, '')
        self.assertEqual(label_key.description, '')

    def test_constructor_WithNonAsciiChars(self):
        key = '值'
        description = '测试用键'
        label_key = label_key_module.LabelKey(key, description)

        self.assertIsNotNone(label_key)
        self.assertEqual(label_key.key, key)
        self.assertEqual(label_key.description, description)
