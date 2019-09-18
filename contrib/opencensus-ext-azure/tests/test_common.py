# Copyright 2019, OpenCensus Authors
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

from opencensus.ext.azure import common


class TestLocalFileBlob(unittest.TestCase):
    def test_validate_key(self):
        key = '1234abcd-5678-4efa-8abc-1234567890ab'
        self.assertIsNone(common.validate_key(key))

    def test_invalid_key_none(self):
        key = None
        self.assertRaises(ValueError, lambda: common.validate_key(key))

    def test_invalid_key_empty(self):
        key = ''
        self.assertRaises(ValueError, lambda: common.validate_key(key))

    def test_invalid_key_length(self):
        key = '1234abcd-5678-4efa-8abc-1234567890abz'
        self.assertRaises(ValueError, lambda: common.validate_key(key))

    def test_invalid_key_dashes(self):
        key = '1234abcda5678-4efa-8abc-1234567890ab'
        self.assertRaises(ValueError, lambda: common.validate_key(key))

    def test_invalid_key_section1_length(self):
        key = '1234abcda-678-4efa-8abc-1234567890ab'
        self.assertRaises(ValueError, lambda: common.validate_key(key))

    def test_invalid_key_section2_length(self):
        key = '1234abcd-678-a4efa-8abc-1234567890ab'
        self.assertRaises(ValueError, lambda: common.validate_key(key))

    def test_invalid_key_section3_length(self):
        key = '1234abcd-6789-4ef-8cabc-1234567890ab'
        self.assertRaises(ValueError, lambda: common.validate_key(key))

    def test_invalid_key_section4_length(self):
        key = '1234abcd-678-4efa-8bc-11234567890ab'
        self.assertRaises(ValueError, lambda: common.validate_key(key))

    def test_invalid_key_section5_length(self):
        key = '234abcd-678-4efa-8abc-11234567890ab'
        self.assertRaises(ValueError, lambda: common.validate_key(key))

    def test_invalid_key_section1_hex(self):
        key = 'x234abcd-5678-4efa-8abc-1234567890ab'
        self.assertRaises(ValueError, lambda: common.validate_key(key))

    def test_invalid_key_section2_hex(self):
        key = '1234abcd-x678-4efa-8abc-1234567890ab'
        self.assertRaises(ValueError, lambda: common.validate_key(key))

    def test_invalid_key_section3_hex(self):
        key = '1234abcd-5678-4xfa-8abc-1234567890ab'
        self.assertRaises(ValueError, lambda: common.validate_key(key))

    def test_invalid_key_section4_hex(self):
        key = '1234abcd-5678-4xfa-8abc-1234567890ab'
        self.assertRaises(ValueError, lambda: common.validate_key(key))

    def test_invalid_key_section5_hex(self):
        key = '1234abcd-5678-4xfa-8abc-1234567890ab'
        self.assertRaises(ValueError, lambda: common.validate_key(key))

    def test_invalid_key_version(self):
        key = '1234abcd-5678-6efa-8abc-1234567890ab'
        self.assertRaises(ValueError, lambda: common.validate_key(key))

    def test_invalid_key_variant(self):
        key = '1234abcd-5678-4efa-2abc-1234567890ab'
        self.assertRaises(ValueError, lambda: common.validate_key(key))
