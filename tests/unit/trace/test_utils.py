#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2017, OpenCensus Authors
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

from opencensus.trace import utils


class TestUtils(unittest.TestCase):

    def test__get_truncatable_str(self):
        str_to_convert = 'test string'
        truncatable_str = utils._get_truncatable_str(str_to_convert)

        expected_str = {'value': str_to_convert, 'truncated_byte_count': 0}

        self.assertEqual(expected_str, truncatable_str)

    def test__get_truncatable_str_length_exceeds(self):
        max_len = 5
        str_to_convert = 'length exceeded'
        patch = mock.patch('opencensus.trace.utils.MAX_LENGTH', max_len)

        with patch:
            truncatable_str = utils._get_truncatable_str(str_to_convert)

        expected_str = {'value': 'lengt', 'truncated_byte_count': 10}

        self.assertEqual(expected_str, truncatable_str)

    def test_check_str_length(self):
        limit = 5

        str_to_check = u'test测试'

        (result, truncated_byte_count) = utils.check_str_length(
            str_to_check, limit)

        expected_result = 'test'

        # Should only have 4 bytes remained, dropped off the invalid part if
        # truncated in the middle of a character.
        self.assertEqual(expected_result, result)
        self.assertEqual(truncated_byte_count, 5)
