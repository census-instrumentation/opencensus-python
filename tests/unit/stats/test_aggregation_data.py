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
import mock
from opencensus.stats import aggregation_data as aggregation_data_module


class TestBaseAggregationData(unittest.TestCase):

    def test_constructor(self):
        aggregation_data = 0
        base_aggregation_data = aggregation_data_module.BaseAggregationData(aggregation_data=aggregation_data)

        self.assertEqual(0, base_aggregation_data.aggregation_data)


class TestSumAggregationData(unittest.TestCase):

    def test_constructor(self):
        sum_data = 1
        sum_aggregation_data = aggregation_data_module.SumAggregationDataFloat(sum_data=sum_data)

        self.assertEqual(1, sum_aggregation_data.sum_data)

    def test_add_sample(self):
        sum_data = 1
        value = 3
        sum_aggregation_data = aggregation_data_module.SumAggregationDataFloat(sum_data=sum_data)
        sum_aggregation_data.add_sample(value=value)

        self.assertEqual(4, sum_aggregation_data.sum_data)


class TestCountAggregationData(unittest.TestCase):

    def test_constructor(self):
        count_data = 0
        count_aggregation_data = aggregation_data_module.CountAggregationData(count_data=count_data)

        self.assertEqual(0, count_aggregation_data.count_data)

    def test_add_sample(self):
        count_data = 0
        count_aggregation_data = aggregation_data_module.CountAggregationData(count_data=count_data)
        count_aggregation_data.add_sample(10)

        self.assertEqual(1, count_aggregation_data.count_data)


class TestDistributionAggregationData(unittest.TestCase):

    def test_constructor(self):
        mean_data = 1
        count_data = 0
        _min = 0
        _max = 1
        sum_of_sqd_deviations = mock.Mock()
        counts_per_bucket = [1, 1, 1]
        bounds = [0, 1/2, 1]

        distribution_aggregation_data = aggregation_data_module.DistributionAggregationData(
            mean_data=mean_data,
            count_data=count_data,
            min_= _min,
            max_ = _max,
            sum_of_sqd_deviations=sum_of_sqd_deviations,
            counts_per_bucket=counts_per_bucket,
            bounds=bounds
        )

        self.assertEqual(1, distribution_aggregation_data.mean_data)
        self.assertEqual(0, distribution_aggregation_data.count_data)
        self.assertEqual(0, distribution_aggregation_data.min)
        self.assertEqual(1, distribution_aggregation_data.max)
        self.assertEqual(sum_of_sqd_deviations, distribution_aggregation_data.sum_of_sqd_deviations)
        self.assertEqual([1, 1, 1], distribution_aggregation_data.counts_per_bucket)
        self.assertEqual([0, 1/2, 1], distribution_aggregation_data.bounds)

    def test_add_sample(self):
        mean_data = 1.0
        count_data = 0
        _min = 0
        _max = 1
        sum_of_sqd_deviations = 2
        counts_per_bucket = [1, 1, 1, 1]
        bounds = [0, 0.5, 1, 1.5]

        value = 3

        distribution_aggregation_data = aggregation_data_module.DistributionAggregationData(
            mean_data=mean_data,
            count_data=count_data,
            min_= _min,
            max_ = _max,
            sum_of_sqd_deviations=sum_of_sqd_deviations,
            counts_per_bucket=counts_per_bucket,
            bounds=bounds
        )

        distribution_aggregation_data.add_sample(value=value)
        self.assertEqual(0, distribution_aggregation_data.min)
        self.assertEqual(3, distribution_aggregation_data.max)
        self.assertEqual(1, distribution_aggregation_data.count_data)
        self.assertEqual(value, distribution_aggregation_data.mean_data)

        count_data = 1
        distribution_aggregation_data = aggregation_data_module.DistributionAggregationData(
            mean_data=mean_data,
            count_data=count_data,
            min_= _min,
            max_ = _max,
            sum_of_sqd_deviations=sum_of_sqd_deviations,
            counts_per_bucket=counts_per_bucket,
            bounds=bounds
        )

        distribution_aggregation_data.add_sample(value=value)
        self.assertEqual(2, distribution_aggregation_data.count_data)
        self.assertEqual(2.0, distribution_aggregation_data.mean_data)
        self.assertEqual(4.0, distribution_aggregation_data.sum_of_sqd_deviations)

    def test_increment_bucket_count(self):
        mean_data = mock.Mock()
        count_data = mock.Mock()
        _min = 0
        _max = 1
        sum_of_sqd_deviations = mock.Mock()
        counts_per_bucket = [0]
        bounds = []

        value = 1

        distribution_aggregation_data = aggregation_data_module.DistributionAggregationData(
            mean_data=mean_data,
            count_data=count_data,
            min_= _min,
            max_ = _max,
            sum_of_sqd_deviations=sum_of_sqd_deviations,
            counts_per_bucket=counts_per_bucket,
            bounds=bounds
        )

        distribution_aggregation_data.increment_bucket_count(value=value)
        self.assertEqual([1], distribution_aggregation_data.counts_per_bucket)

        counts_per_bucket = [1, 1]
        bounds = [1/4, 3/2]

        distribution_aggregation_data = aggregation_data_module.DistributionAggregationData(
            mean_data=mean_data,
            count_data=count_data,
            min_= _min,
            max_ = _max,
            sum_of_sqd_deviations=sum_of_sqd_deviations,
            counts_per_bucket=counts_per_bucket,
            bounds=bounds
        )

        distribution_aggregation_data.increment_bucket_count(value=value)
        self.assertEqual([1, 2], distribution_aggregation_data.counts_per_bucket)

        bounds = [1/4, 1/2]

        distribution_aggregation_data = aggregation_data_module.DistributionAggregationData(
            mean_data=mean_data,
            count_data=count_data,
            min_= _min,
            max_ = _max,
            sum_of_sqd_deviations=sum_of_sqd_deviations,
            counts_per_bucket=counts_per_bucket,
            bounds=bounds
        )

        distribution_aggregation_data.increment_bucket_count(value=value)
        self.assertEqual([1, 3], distribution_aggregation_data.counts_per_bucket)
