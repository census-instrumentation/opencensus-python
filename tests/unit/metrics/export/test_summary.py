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

from six import assertRaisesRegex
import unittest

from opencensus.metrics.export import summary as summary_module


class TestSummary(unittest.TestCase):
    def setUp(self):
        value_at_percentile = [summary_module.ValueAtPercentile(99.5, 10.2)]
        self.snapshot = summary_module.Snapshot(10, 87.07, value_at_percentile)

    def test_constructor(self):
        summary = summary_module.Summary(10, 6.6, self.snapshot)

        self.assertIsNotNone(summary)
        self.assertEqual(summary.count, 10)
        self.assertEqual(summary.sum_data, 6.6)
        self.assertIsNotNone(summary.snapshot)
        self.assertIsInstance(summary.snapshot, summary_module.Snapshot)

    def test_constructor_with_negative_count(self):
        with assertRaisesRegex(self, ValueError, 'count must be non-negative'):
            summary_module.Summary(-10, 87.07, self.snapshot)

    def test_constructor_with_negative_sum_data(self):
        with assertRaisesRegex(self, ValueError,
                               'sum_data must be non-negative'):
            summary_module.Summary(10, -87.07, self.snapshot)

    def test_constructor_with_zero_count_and_sum_data(self):
        with assertRaisesRegex(self, ValueError,
                               'sum_data must be 0 if count is 0'):
            summary_module.Summary(0, 87.07, self.snapshot)

    def test_constructor_with_none_snapshot(self):
        with assertRaisesRegex(self, ValueError, 'snapshot must not be none'):
            summary_module.Summary(10, 87.07, None)


class TestSnapshot(unittest.TestCase):
    def setUp(self):
        self.value_at_percentile = [
            summary_module.ValueAtPercentile(99.5, 10.2)
        ]

        # Invalid value_at_percentile
        self.value_at_percentile1 = summary_module.ValueAtPercentile(
            99.5, 10.2)

    def test_constructor(self):
        snapshot = summary_module.Snapshot(10, 87.07, self.value_at_percentile)

        self.assertIsNotNone(snapshot)
        self.assertEqual(snapshot.count, 10)
        self.assertEqual(snapshot.sum_data, 87.07)
        self.assertIsNotNone(snapshot.value_at_percentiles)
        self.assertEqual(len(snapshot.value_at_percentiles), 1)
        self.assertEqual(snapshot.value_at_percentiles[0].percentile, 99.5)
        self.assertEqual(snapshot.value_at_percentiles[0].value, 10.2)

    def test_constructor_invalid_value_at_percentile(self):
        with self.assertRaises(ValueError):
            summary_module.Snapshot(10, 87.07, self.value_at_percentile1)

    def test_constructor_empty_value_at_percentile(self):
        snapshot = summary_module.Snapshot(10, 87.07)

        self.assertIsNotNone(snapshot)
        self.assertIsNotNone(snapshot.value_at_percentiles)
        self.assertEqual(len(snapshot.value_at_percentiles), 0)

    def test_constructor_with_negative_count(self):
        with assertRaisesRegex(self, ValueError, 'count must be non-negative'):
            summary_module.Snapshot(-10, 87.07, self.value_at_percentile)

    def test_constructor_with_negative_sum_data(self):
        with assertRaisesRegex(self, ValueError,
                               'sum_data must be non-negative'):
            summary_module.Snapshot(10, -87.07, self.value_at_percentile)

    def test_constructor_with_zero_count(self):
        with assertRaisesRegex(self, ValueError,
                               'sum_data must be 0 if count is 0'):
            summary_module.Snapshot(0, 87.07, self.value_at_percentile)

    def test_constructor_with_zero_count_and_sum_data(self):
        summary_module.Snapshot(0, 0, self.value_at_percentile)

    def test_constructor_with_none_count_sum(self):
        snapshot = summary_module.Snapshot(None, None,
                                           self.value_at_percentile)

        self.assertIsNotNone(snapshot)
        self.assertIsNone(snapshot.count)
        self.assertIsNone(snapshot.sum_data)
        self.assertIsNotNone(snapshot.value_at_percentiles)
        self.assertEqual(len(snapshot.value_at_percentiles), 1)


class TestValueAtPercentile(unittest.TestCase):
    def test_constructor(self):
        value_at_percentile = summary_module.ValueAtPercentile(99.5, 10.2)

        self.assertIsNotNone(value_at_percentile)
        self.assertEqual(value_at_percentile.value, 10.2)
        self.assertEqual(value_at_percentile.percentile, 99.5)

    def test_constructor_invalid_percentile(self):
        with self.assertRaises(ValueError):
            summary_module.ValueAtPercentile(100.1, 10.2)

    def test_constructor_invalid_value(self):
        with assertRaisesRegex(self, ValueError, 'value must be non-negative'):
            summary_module.ValueAtPercentile(99.5, -10.2)
