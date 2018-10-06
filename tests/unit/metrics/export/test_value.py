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
from opencensus.metrics.export import summary as summary_module
from opencensus.metrics.export import value as value_module


class TestValue(unittest.TestCase):

    def test_create_double_value(self):
        double_value = value_module.Value.double_value(-34.56)

        self.assertIsNotNone(double_value)
        self.assertIsInstance(double_value, value_module.ValueDouble)
        self.assertEqual(double_value.value, -34.56)

    def test_create_long_value(self):
        long_value = value_module.Value.long_value(123456789)

        self.assertIsNotNone(long_value)
        self.assertIsInstance(long_value, value_module.ValueLong)
        self.assertEqual(long_value.value, 123456789)

    def test_create_summary_value(self):
        value_at_percentile = [summary_module.ValueAtPercentile(99.5, 10.2)]
        snapshot = summary_module.Snapshot(10, 87.07, value_at_percentile)
        summary = summary_module.Summary(10, 6.6, snapshot)

        summary_value = value_module.Value.summary_value(summary)

        self.assertIsNotNone(summary_value)
        self.assertIsInstance(summary_value, value_module.ValueSummary)
        self.assertEqual(summary_value.value, summary)
