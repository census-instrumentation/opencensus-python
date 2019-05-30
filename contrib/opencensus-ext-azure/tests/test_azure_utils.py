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
from opencensus.ext.azure.common import utils


class TestUtils(unittest.TestCase):
    def test_microseconds_to_duration(self):
        us_to_duration = utils.microseconds_to_duration
        self.assertEqual(us_to_duration(0), '0.00:00:00.000')
        self.assertEqual(us_to_duration(1000000), '0.00:00:01.000')
        self.assertEqual(us_to_duration(60 * 1000000), '0.00:01:00.000')
        self.assertEqual(us_to_duration(60 * 60 * 1000000), '0.01:00:00.000')
        self.assertEqual(us_to_duration(86400 * 1000000), '1.00:00:00.000')

    def test_timestamp_to_duration(self):
        self.assertEqual(utils.timestamp_to_duration(
                '2010-10-24T07:28:38.123456Z',
                '2010-10-24T07:28:38.234567Z',
            ), '0.00:00:00.111')

    def test_timestamp_to_iso_str(self):
        self.assertEqual(utils.timestamp_to_iso_str(
                1287905318.123456,
            ), '2010-10-24T07:28:38.123456Z')

    def test_url_to_dependency_name(self):
        self.assertEqual(
            utils.url_to_dependency_name(
                'https://www.wikipedia.org/wiki/Rabbit'
            ),
            'www.wikipedia.org')
