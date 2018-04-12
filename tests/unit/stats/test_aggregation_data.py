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


class TestMeanAggregationData(unittest.TestCase):

    def test_constructor(self):
        mean_data = 0
        count_data = 0
        mean_aggregation_data = aggregation_data_module.MeanAggregationData(mean_data=mean_data, count_data=count_data)

        self.assertEqual(0, mean_aggregation_data.mean_data)
        self.assertEqual(0, mean_aggregation_data.count_data)

    def test_add_sample(self):
        mean_data = 1
        count_data = 0
        mean_aggregation_data = aggregation_data_module.MeanAggregationData(mean_data=mean_data, count_data=count_data)
        mean_aggregation_data.add_sample(1)

        self.assertEqual(1, mean_aggregation_data.mean_data)
        self.assertEqual(1, mean_aggregation_data.count_data)

''' need distribution test'''