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

import mock
import unittest

from opencensus.stats import aggregation as aggregation_module
from opencensus.stats import measure as measure_module
from opencensus.metrics.export import value


class TestSumAggregation(unittest.TestCase):
    def test_new_aggregation_data_defaults(self):
        measure = mock.Mock(spec=measure_module.MeasureInt)
        sum_aggregation = aggregation_module.SumAggregation()
        agg_data = sum_aggregation.new_aggregation_data(measure)
        self.assertEqual(0, agg_data.sum_data)
        self.assertEqual(value.ValueLong, agg_data.value_type)

    def test_new_aggregation_data_explicit(self):
        measure = mock.Mock(spec=measure_module.MeasureInt)
        sum_aggregation = aggregation_module.SumAggregation(sum=1)
        agg_data = sum_aggregation.new_aggregation_data(measure)
        self.assertEqual(1, agg_data.sum_data)
        self.assertEqual(value.ValueLong, agg_data.value_type)

    def test_new_aggregation_data_float(self):
        measure = mock.Mock(spec=measure_module.MeasureFloat)
        sum_aggregation = aggregation_module.SumAggregation()
        agg_data = sum_aggregation.new_aggregation_data(measure)
        self.assertEqual(0, agg_data.sum_data)
        self.assertEqual(value.ValueDouble, agg_data.value_type)

    def test_new_aggregation_data_bad(self):
        measure = mock.Mock(spec=measure_module.BaseMeasure)
        sum_aggregation = aggregation_module.SumAggregation()
        with self.assertRaises(ValueError):
            sum_aggregation.new_aggregation_data(measure)


class TestCountAggregation(unittest.TestCase):
    def test_new_aggregation_data_defaults(self):
        count_aggregation = aggregation_module.CountAggregation()
        agg_data = count_aggregation.new_aggregation_data()
        self.assertEqual(0, agg_data.count_data)

    def test_new_aggregation_data_explicit(self):
        count_aggregation = aggregation_module.CountAggregation(count=4)
        agg_data = count_aggregation.new_aggregation_data()
        self.assertEqual(4, agg_data.count_data)


class TestLastValueAggregation(unittest.TestCase):
    def test_new_aggregation_data_defaults(self):
        measure = mock.Mock(spec=measure_module.MeasureInt)
        last_value_aggregation = aggregation_module.LastValueAggregation()
        agg_data = last_value_aggregation.new_aggregation_data(measure)
        self.assertEqual(0, agg_data.value)
        self.assertEqual(value.ValueLong, agg_data.value_type)

    def test_new_aggregation_data_explicit(self):
        measure = mock.Mock(spec=measure_module.MeasureInt)
        last_value_aggregation = aggregation_module.LastValueAggregation(
            value=6)
        agg_data = last_value_aggregation.new_aggregation_data(measure)
        self.assertEqual(6, agg_data.value)
        self.assertEqual(value.ValueLong, agg_data.value_type)

    def test_new_aggregation_data_float(self):
        measure = mock.Mock(spec=measure_module.MeasureFloat)
        last_value_aggregation = aggregation_module.LastValueAggregation()
        agg_data = last_value_aggregation.new_aggregation_data(measure)
        self.assertEqual(0, agg_data.value)
        self.assertEqual(value.ValueDouble, agg_data.value_type)

    def test_new_aggregation_data_bad(self):
        measure = mock.Mock(spec=measure_module.BaseMeasure)
        last_value_aggregation = aggregation_module.LastValueAggregation()
        with self.assertRaises(ValueError):
            last_value_aggregation.new_aggregation_data(measure)


class TestDistributionAggregation(unittest.TestCase):
    def test_new_aggregation_data_defaults(self):
        distribution_aggregation = aggregation_module.DistributionAggregation()
        agg_data = distribution_aggregation.new_aggregation_data()
        self.assertEqual([], agg_data.bounds)

    def test_new_aggregation_data_explicit(self):
        boundaries = [1, 2]
        distribution_aggregation = aggregation_module.DistributionAggregation(
            boundaries=boundaries)
        agg_data = distribution_aggregation.new_aggregation_data()
        self.assertEqual(boundaries, agg_data.bounds)

    def test_init_bad_boundaries(self):
        """Check that boundaries must be sorted and unique."""
        with self.assertRaises(ValueError):
            aggregation_module.DistributionAggregation([1, 3, 2])
        with self.assertRaises(ValueError):
            aggregation_module.DistributionAggregation([1, 1, 2])

    def test_init_negative_boundaries(self):
        """Check that non-positive boundaries are dropped."""
        da = aggregation_module.DistributionAggregation([-2, -1, 0, 1, 2])
        self.assertEqual(da.new_aggregation_data().bounds, [1, 2])

        da2 = aggregation_module.DistributionAggregation([-2, -1])
        self.assertEqual(da2.new_aggregation_data().bounds, [])
