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

from datetime import datetime
import unittest

from opencensus.common import utils as common_utils
from opencensus.ext.ocagent import utils


class TestUtils(unittest.TestCase):
    def test_datetime_str_to_proto_ts_conversion(self):
        now = datetime.utcnow()
        delta = now - datetime(1970, 1, 1)
        expected_seconds = int(delta.total_seconds())
        expected_nanos = delta.microseconds * 1000

        proto_ts = utils.proto_ts_from_datetime_str(
            common_utils.to_iso_str(now))
        self.assertEqual(proto_ts.seconds, int(expected_seconds))
        self.assertEqual(proto_ts.nanos, expected_nanos)

    def test_datetime_str_to_proto_ts_conversion_none(self):
        proto_ts = utils.proto_ts_from_datetime_str(None)
        self.assertEqual(proto_ts.seconds, 0)
        self.assertEqual(proto_ts.nanos, 0)

    def test_datetime_str_to_proto_ts_conversion_empty(self):
        proto_ts = utils.proto_ts_from_datetime_str('')
        self.assertEqual(proto_ts.seconds, 0)
        self.assertEqual(proto_ts.nanos, 0)

    def test_datetime_str_to_proto_ts_conversion_invalid(self):
        proto_ts = utils.proto_ts_from_datetime_str('2018 08 22 T 11:53')
        self.assertEqual(proto_ts.seconds, 0)
        self.assertEqual(proto_ts.nanos, 0)

    def test_datetime_to_proto_ts_conversion_none(self):
        proto_ts = utils.proto_ts_from_datetime(None)
        self.assertEqual(proto_ts.seconds, 0)
        self.assertEqual(proto_ts.nanos, 0)

    def test_datetime_to_proto_ts_conversion(self):
        now = datetime.utcnow()
        delta = now - datetime(1970, 1, 1)
        expected_seconds = int(delta.total_seconds())
        expected_nanos = delta.microseconds * 1000

        proto_ts = utils.proto_ts_from_datetime(now)
        self.assertEqual(proto_ts.seconds, int(expected_seconds))
        self.assertEqual(proto_ts.nanos, expected_nanos)

    def test_datetime_to_proto_ts_conversion_zero(self):
        zero = datetime(1970, 1, 1)

        proto_ts = utils.proto_ts_from_datetime(zero)
        self.assertEqual(proto_ts.seconds, 0)
        self.assertEqual(proto_ts.nanos, 0)
