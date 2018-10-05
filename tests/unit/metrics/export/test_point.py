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
from datetime import datetime
from opencensus.metrics.export import point as point_module
from opencensus.metrics.export import summary as summary_module
from opencensus.metrics.export import value as value_module


class TestPoint(unittest.TestCase):

    def setUp(self):
        self.double_value = value_module.Value.double_value(55.5)
        self.long_value = value_module.Value.long_value(9876543210)
        self.timestamp = datetime.utcnow().isoformat() + 'Z'

        value_at_percentile = [summary_module.ValueAtPercentile(99.5, 10.2)]
        snapshot = summary_module.Snapshot(10, 87.07, value_at_percentile)
        self.summary = summary_module.Summary(10, 6.6, snapshot)
        self.summary_value = value_module.Value.summary_value(self.summary)

    def test_point_with_double_value(self):
        point = point_module.Point(self.double_value, self.timestamp)

        self.assertIsNotNone(point)
        self.assertEqual(point.timestamp, self.timestamp)

        self.assertIsInstance(point.value, value_module.ValueDouble)
        self.assertIsNotNone(point.value)
        self.assertEqual(point.value, self.double_value)
        self.assertEqual(point.value.get_value, 55.5)

    def test_point_with_long_value(self):
        point = point_module.Point(self.long_value, self.timestamp)

        self.assertIsNotNone(point)
        self.assertEqual(point.timestamp, self.timestamp)

        self.assertIsInstance(point.value, value_module.ValueLong)
        self.assertIsNotNone(point.value)
        self.assertEqual(point.value, self.long_value)
        self.assertEqual(point.value.get_value, 9876543210)

    def test_point_with_summary_value(self):
        point = point_module.Point(self.summary_value, self.timestamp)

        self.assertIsNotNone(point)
        self.assertEqual(point.timestamp, self.timestamp)

        self.assertIsInstance(point.value, value_module.ValueSummary)
        self.assertIsNotNone(point.value)
        self.assertEqual(point.value, self.summary_value)
        self.assertEqual(point.value.get_value, self.summary)
