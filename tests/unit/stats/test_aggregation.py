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

from opencensus.stats import aggregation as aggregation_module


class TestBaseAggregation(unittest.TestCase):
    def test_constructor_defaults(self):
        base_aggregation = aggregation_module.BaseAggregation()

        self.assertEqual(aggregation_module.Type.NONE,
                         base_aggregation.aggregation_type)
        self.assertEqual([], base_aggregation.buckets)

    def test_constructor_explicit(self):

        buckets = ["test"]
        base_aggregation = aggregation_module.BaseAggregation(buckets=buckets)

        self.assertEqual(aggregation_module.Type.NONE,
                         base_aggregation.aggregation_type)
        self.assertEqual(["test"], base_aggregation.buckets)


class TestSumAggregation(unittest.TestCase):
    def test_constructor_defaults(self):
        sum_aggregation = aggregation_module.SumAggregation()

        self.assertEqual(0, sum_aggregation.sum.sum_data)
        self.assertEqual(aggregation_module.Type.SUM,
                         sum_aggregation.aggregation_type)

    def test_constructor_explicit(self):
        sum = 1

        sum_aggregation = aggregation_module.SumAggregation(sum=sum)

        self.assertEqual(1, sum_aggregation.sum.sum_data)
        self.assertEqual(aggregation_module.Type.SUM,
                         sum_aggregation.aggregation_type)


class TestCountAggregation(unittest.TestCase):
    def test_constructor_defaults(self):
        count_aggregation = aggregation_module.CountAggregation()

        self.assertEqual(0, count_aggregation.count.count_data)
        self.assertEqual(aggregation_module.Type.COUNT,
                         count_aggregation.aggregation_type)

    def test_constructor_explicit(self):
        count = 4

        count_aggregation = aggregation_module.CountAggregation(count=count)

        self.assertEqual(4, count_aggregation.count.count_data)
        self.assertEqual(aggregation_module.Type.COUNT,
                         count_aggregation.aggregation_type)


class TestLastValueAggregation(unittest.TestCase):
    def test_constructor_defaults(self):
        last_value_aggregation = aggregation_module.LastValueAggregation()

        self.assertEqual(0, last_value_aggregation.value)
        self.assertEqual(aggregation_module.Type.LASTVALUE,
                         last_value_aggregation.aggregation_type)

    def test_constructor_explicit(self):
        val = 16
        last_value_aggregation = aggregation_module.LastValueAggregation(
            value=val)

        self.assertEqual(16, last_value_aggregation.value)
        self.assertEqual(aggregation_module.Type.LASTVALUE,
                         last_value_aggregation.aggregation_type)


class TestDistributionAggregation(unittest.TestCase):
    def test_constructor_defaults(self):
        distribution_aggregation = aggregation_module.DistributionAggregation()

        self.assertEqual([], distribution_aggregation.boundaries.boundaries)
        self.assertEqual({}, distribution_aggregation.distribution)
        self.assertEqual(aggregation_module.Type.DISTRIBUTION,
                         distribution_aggregation.aggregation_type)

    def test_constructor_explicit(self):
        boundaries = [1, 2]
        distribution = [0, 1, 2]
        distribution_aggregation = aggregation_module.DistributionAggregation(
            boundaries=boundaries, distribution=distribution)

        self.assertEqual([1, 2],
                         distribution_aggregation.boundaries.boundaries)
        self.assertEqual([0, 1, 2], distribution_aggregation.distribution)
        self.assertEqual(aggregation_module.Type.DISTRIBUTION,
                         distribution_aggregation.aggregation_type)

    def test_init_bad_boundaries(self):
        """Check that boundaries must be sorted and unique."""
        with self.assertRaises(ValueError):
            aggregation_module.DistributionAggregation([1, 3, 2])
        with self.assertRaises(ValueError):
            aggregation_module.DistributionAggregation([1, 1, 2])

    def test_init_negative_boundaries(self):
        """Check that non-positive boundaries are dropped."""
        da = aggregation_module.DistributionAggregation([-2, -1, 0, 1, 2])
        self.assertEqual(da.boundaries.boundaries, [1, 2])
        self.assertEqual(da.aggregation_data.bounds, [1, 2])

        da2 = aggregation_module.DistributionAggregation([-2, -1])
        self.assertEqual(da2.boundaries.boundaries, [])
        self.assertEqual(da2.aggregation_data.bounds, [])
