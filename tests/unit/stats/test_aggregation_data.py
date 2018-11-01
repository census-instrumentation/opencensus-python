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

import time
import unittest

import mock

from opencensus.stats import aggregation_data as aggregation_data_module


class TestBaseAggregationData(unittest.TestCase):
    def test_constructor(self):
        aggregation_data = 0
        base_aggregation_data = aggregation_data_module.BaseAggregationData(
            aggregation_data=aggregation_data)

        self.assertEqual(0, base_aggregation_data.aggregation_data)


class TestSumAggregationData(unittest.TestCase):
    def test_constructor(self):
        sum_data = 1
        sum_aggregation_data = aggregation_data_module.SumAggregationDataFloat(
            sum_data=sum_data)

        self.assertEqual(1, sum_aggregation_data.sum_data)

    def test_add_sample(self):
        sum_data = 1
        value = 3
        sum_aggregation_data = aggregation_data_module.SumAggregationDataFloat(
            sum_data=sum_data)
        sum_aggregation_data.add_sample(value, None, None)

        self.assertEqual(4, sum_aggregation_data.sum_data)


class TestCountAggregationData(unittest.TestCase):
    def test_constructor(self):
        count_data = 0
        count_aggregation_data = aggregation_data_module.CountAggregationData(
            count_data=count_data)

        self.assertEqual(0, count_aggregation_data.count_data)

    def test_add_sample(self):
        count_data = 0
        count_aggregation_data = aggregation_data_module.CountAggregationData(
            count_data=count_data)
        count_aggregation_data.add_sample(10, None, None)

        self.assertEqual(1, count_aggregation_data.count_data)


class TestLastValueAggregationData(unittest.TestCase):
    def test_constructor(self):
        value_data = 0
        last_value_aggregation_data =\
            aggregation_data_module.LastValueAggregationData(value=value_data)

        self.assertEqual(0, last_value_aggregation_data.value)

    def test_overwrite_sample(self):
        first_data = 0
        last_value_aggregation_data =\
            aggregation_data_module.LastValueAggregationData(value=first_data)
        self.assertEqual(0, last_value_aggregation_data.value)
        last_value_aggregation_data.add_sample(1, None, None)
        self.assertEqual(1, last_value_aggregation_data.value)


class TestDistributionAggregationData(unittest.TestCase):
    def test_constructor(self):
        mean_data = 1
        count_data = 0
        _min = 0
        _max = 1
        sum_of_sqd_deviations = mock.Mock()
        counts_per_bucket = [1, 1, 1, 1]
        bounds = [0, 1.0 / 2.0, 1]

        dist_agg_data = aggregation_data_module.DistributionAggregationData(
            mean_data=mean_data,
            count_data=count_data,
            min_=_min,
            max_=_max,
            sum_of_sqd_deviations=sum_of_sqd_deviations,
            counts_per_bucket=counts_per_bucket,
            bounds=bounds)

        self.assertEqual(1, dist_agg_data.mean_data)
        self.assertEqual(0, dist_agg_data.count_data)
        self.assertEqual(0, dist_agg_data.min)
        self.assertEqual(1, dist_agg_data.max)
        self.assertEqual(sum_of_sqd_deviations,
                         dist_agg_data.sum_of_sqd_deviations)
        self.assertEqual([1, 1, 1, 1], dist_agg_data.counts_per_bucket)
        self.assertEqual([0, 1.0 / 2.0, 1], dist_agg_data.bounds)

        self.assertIsNotNone(dist_agg_data.sum)
        self.assertEqual(0, dist_agg_data.variance)

    def test_init_bad_bucket_counts(self):
        # Check that len(counts_per_bucket) == len(bounds) + 1
        with self.assertRaises(ValueError):
            aggregation_data_module.DistributionAggregationData(
                mean_data=mock.Mock(),
                count_data=mock.Mock(),
                min_=mock.Mock(),
                max_=mock.Mock(),
                sum_of_sqd_deviations=mock.Mock(),
                counts_per_bucket=[0, 0, 0],
                bounds=[0, 1, 2])

        # And check that we don't throw given the right args
        aggregation_data_module.DistributionAggregationData(
            mean_data=mock.Mock(),
            count_data=mock.Mock(),
            min_=mock.Mock(),
            max_=mock.Mock(),
            sum_of_sqd_deviations=mock.Mock(),
            counts_per_bucket=[0, 0, 0, 0],
            bounds=[0, 1, 2])

    def test_constructor_with_exemplar(self):
        timestamp = time.time()
        attachments = {"One": "one", "Two": "two"}
        exemplar_1 = aggregation_data_module.Exemplar(4, timestamp,
                                                      attachments)
        exemplar_2 = aggregation_data_module.Exemplar(5, timestamp,
                                                      attachments)
        mean_data = 1
        count_data = 0
        _min = 0
        _max = 1
        sum_of_sqd_deviations = mock.Mock()
        counts_per_bucket = [1, 1, 1, 1]
        bounds = [0, 1.0 / 2.0, 1]
        exemplars = [exemplar_1, exemplar_2]

        dist_agg_data = aggregation_data_module.DistributionAggregationData(
            mean_data=mean_data,
            count_data=count_data,
            min_=_min,
            max_=_max,
            sum_of_sqd_deviations=sum_of_sqd_deviations,
            exemplars=exemplars,
            counts_per_bucket=counts_per_bucket,
            bounds=bounds)

        self.assertEqual(1, dist_agg_data.mean_data)
        self.assertEqual(0, dist_agg_data.count_data)
        self.assertEqual(0, dist_agg_data.min)
        self.assertEqual(1, dist_agg_data.max)
        self.assertEqual(sum_of_sqd_deviations,
                         dist_agg_data.sum_of_sqd_deviations)
        self.assertEqual([1, 1, 1, 1], dist_agg_data.counts_per_bucket)
        self.assertEqual([exemplar_1, exemplar_2], dist_agg_data.exemplars[3])
        self.assertEqual([0, 1.0 / 2.0, 1], dist_agg_data.bounds)

        self.assertIsNotNone(dist_agg_data.sum)
        self.assertEqual(0, dist_agg_data.variance)

    def test_exemplar(self):
        timestamp = time.time()
        attachments = {"One": "one", "Two": "two"}
        exemplar = aggregation_data_module.Exemplar(4, timestamp, attachments)

        self.assertEqual(4, exemplar.value)
        self.assertEqual(timestamp, exemplar.timestamp)
        self.assertEqual(attachments, exemplar.attachments)

    def test_exemplar_null_attachments(self):
        timestamp = time.time()

        with self.assertRaisesRegexp(TypeError,
                                     'attachments should not be empty'):
            aggregation_data_module.Exemplar(6, timestamp, None)

    def test_exemplar_null_attachment_key(self):
        timestamp = time.time()
        attachment = {None: "one", "Two": "two"}

        with self.assertRaisesRegexp(
                TypeError,
                'attachment key should not be empty and should be a string'):
            aggregation_data_module.Exemplar(6, timestamp, attachment)

    def test_exemplar_null_attachment_value(self):
        timestamp = time.time()
        attachment = {"One": "one", "Two": None}

        with self.assertRaisesRegexp(
                TypeError,
                'attachment value should not be empty and should be a string'):
            aggregation_data_module.Exemplar(6, timestamp, attachment)

    def test_exemplar_int_attachment_key(self):
        timestamp = time.time()
        attachment = {1: "one", "Two": "two"}

        with self.assertRaisesRegexp(
                TypeError,
                'attachment key should not be empty and should be a string'):
            aggregation_data_module.Exemplar(6, timestamp, attachment)

    def test_exemplar_int_attachment_value(self):
        timestamp = time.time()
        attachment = {"One": "one", "Two": 2}

        with self.assertRaisesRegexp(
                TypeError,
                'attachment value should not be empty and should be a string'):
            aggregation_data_module.Exemplar(6, timestamp, attachment)

    def test_variance(self):
        mean_data = mock.Mock()
        count_data = 0
        _min = mock.Mock()
        _max = mock.Mock()
        sum_of_sqd_deviations = mock.Mock()
        counts_per_bucket = [1, 1, 1, 1]
        bounds = [0, 1.0 / 2.0, 1]
        dist_agg_data = aggregation_data_module.DistributionAggregationData(
            mean_data=mean_data,
            count_data=count_data,
            min_=_min,
            max_=_max,
            sum_of_sqd_deviations=sum_of_sqd_deviations,
            counts_per_bucket=counts_per_bucket,
            bounds=bounds)
        self.assertEqual(0, dist_agg_data.variance)

        count_data = 2
        sum_of_sqd_deviations = 2
        dist_agg_data = aggregation_data_module.DistributionAggregationData(
            mean_data=mean_data,
            count_data=count_data,
            min_=_min,
            max_=_max,
            sum_of_sqd_deviations=sum_of_sqd_deviations,
            counts_per_bucket=counts_per_bucket,
            bounds=bounds)
        self.assertEqual(2.0, dist_agg_data.variance)

    def test_add_sample(self):
        mean_data = 1.0
        count_data = 0
        _min = 0
        _max = 1
        sum_of_sqd_deviations = 2
        counts_per_bucket = [1, 1, 1, 1, 1]
        bounds = [0, 0.5, 1, 1.5]

        value = 3

        dist_agg_data = aggregation_data_module.DistributionAggregationData(
            mean_data=mean_data,
            count_data=count_data,
            min_=_min,
            max_=_max,
            sum_of_sqd_deviations=sum_of_sqd_deviations,
            counts_per_bucket=counts_per_bucket,
            bounds=bounds)

        dist_agg_data.add_sample(value, None, None)
        self.assertEqual(0, dist_agg_data.min)
        self.assertEqual(3, dist_agg_data.max)
        self.assertEqual(1, dist_agg_data.count_data)
        self.assertEqual(value, dist_agg_data.mean_data)

        count_data = 1
        dist_agg_data = aggregation_data_module.DistributionAggregationData(
            mean_data=mean_data,
            count_data=count_data,
            min_=_min,
            max_=_max,
            sum_of_sqd_deviations=sum_of_sqd_deviations,
            counts_per_bucket=counts_per_bucket,
            bounds=bounds)

        dist_agg_data.add_sample(value, None, None)
        self.assertEqual(2, dist_agg_data.count_data)
        self.assertEqual(2.0, dist_agg_data.mean_data)
        self.assertEqual(4.0, dist_agg_data.sum_of_sqd_deviations)
        self.assertIsNot(0, dist_agg_data.count_data)

        value_2 = -1
        dist_agg_data.add_sample(value_2, None, None)
        self.assertEqual(value_2, dist_agg_data.min)

    def test_add_sample_attachment(self):
        mean_data = 1.0
        count_data = 1
        _min = 0
        _max = 1
        sum_of_sqd_deviations = 2
        counts_per_bucket = [1, 1, 1, 1, 1]
        bounds = [0, 0.5, 1, 1.5]

        value = 3
        timestamp = time.time()
        attachments = {"One": "one", "Two": "two"}
        exemplar_1 = aggregation_data_module.Exemplar(4, timestamp,
                                                      attachments)

        dist_agg_data = aggregation_data_module.DistributionAggregationData(
            mean_data=mean_data,
            count_data=count_data,
            min_=_min,
            max_=_max,
            sum_of_sqd_deviations=sum_of_sqd_deviations,
            counts_per_bucket=counts_per_bucket,
            bounds=bounds,
            exemplars=exemplar_1)

        self.assertEqual({4: exemplar_1}, dist_agg_data.exemplars)

        dist_agg_data.add_sample(value, timestamp, attachments)
        self.assertEqual(0, dist_agg_data.min)
        self.assertEqual(3, dist_agg_data.max)
        self.assertEqual(2, dist_agg_data.count_data)
        self.assertEqual(2.0, dist_agg_data.mean_data)
        self.assertEqual(3, dist_agg_data.exemplars[4].value)

        count_data = 4
        dist_agg_data = aggregation_data_module.DistributionAggregationData(
            mean_data=mean_data,
            count_data=count_data,
            min_=_min,
            max_=_max,
            sum_of_sqd_deviations=sum_of_sqd_deviations,
            counts_per_bucket=[2, 1, 2, 1, 1, 1],
            bounds=[1, 2, 3, 4, 5])

        dist_agg_data.add_sample(value, timestamp, attachments)
        self.assertEqual(5, dist_agg_data.count_data)
        self.assertEqual(1.4, dist_agg_data.mean_data)
        self.assertEqual(5.2, dist_agg_data.sum_of_sqd_deviations)
        self.assertIsNot(0, dist_agg_data.count_data)
        self.assertEqual(3, dist_agg_data.exemplars[3].value)

    def test_increment_bucket_count(self):
        mean_data = mock.Mock()
        count_data = mock.Mock()
        _min = 0
        _max = 1
        sum_of_sqd_deviations = mock.Mock()
        counts_per_bucket = [0]
        bounds = []

        value = 1

        dist_agg_data = aggregation_data_module.DistributionAggregationData(
            mean_data=mean_data,
            count_data=count_data,
            min_=_min,
            max_=_max,
            sum_of_sqd_deviations=sum_of_sqd_deviations,
            counts_per_bucket=counts_per_bucket,
            bounds=bounds)

        dist_agg_data.increment_bucket_count(value=value)
        self.assertEqual([1], dist_agg_data.counts_per_bucket)

        counts_per_bucket = [1, 1, 1]
        bounds = [1.0 / 4.0, 3.0 / 2.0]

        dist_agg_data = aggregation_data_module.DistributionAggregationData(
            mean_data=mean_data,
            count_data=count_data,
            min_=_min,
            max_=_max,
            sum_of_sqd_deviations=sum_of_sqd_deviations,
            counts_per_bucket=counts_per_bucket,
            bounds=bounds)

        dist_agg_data.increment_bucket_count(value=value)
        self.assertEqual([1, 2, 1], dist_agg_data.counts_per_bucket)

        bounds = [1.0 / 4.0, 1.0 / 2.0]

        dist_agg_data = aggregation_data_module.DistributionAggregationData(
            mean_data=mean_data,
            count_data=count_data,
            min_=_min,
            max_=_max,
            sum_of_sqd_deviations=sum_of_sqd_deviations,
            counts_per_bucket=counts_per_bucket,
            bounds=bounds)

        dist_agg_data.increment_bucket_count(value=value)
        self.assertEqual([1, 2, 2], dist_agg_data.counts_per_bucket)
