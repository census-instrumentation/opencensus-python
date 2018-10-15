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
from opencensus.metrics import label_value as label_value_module


class TestLabelValue(unittest.TestCase):
    def test_constructor(self):
        value = 'value1'
        label_value = label_value_module.LabelValue(value)

        self.assertIsNotNone(label_value)
        self.assertEqual(label_value.value, value)

    def test_constructor_None(self):
        label_value = label_value_module.LabelValue()

        self.assertIsNotNone(label_value)
        self.assertIsNone(label_value.value)

    def test_constructor_Empty(self):
        value = ''
        label_value = label_value_module.LabelValue(value)

        self.assertIsNotNone(label_value)
        self.assertEqual(label_value.value, '')

    def test_constructor_WithNonAsciiChars(self):
        value = '值'
        label_value = label_value_module.LabelValue(value)

        self.assertIsNotNone(label_value)
        self.assertEqual(label_value.value, value)
