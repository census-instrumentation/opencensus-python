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
import time
import unittest

import mock

from opencensus.metrics.export import point
from opencensus.metrics.export import value
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

    def test_to_point(self):
        sum_data = 12.345
        timestamp = datetime(1970, 1, 1)
        agg = aggregation_data_module.SumAggregationDataFloat(sum_data)
        converted_point = agg.to_point(timestamp)
        self.assertTrue(isinstance(converted_point, point.Point))
        self.assertTrue(isinstance(converted_point.value, value.ValueDouble))
        self.assertEqual(converted_point.value.value, sum_data)
        self.assertEqual(converted_point.timestamp, timestamp)


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

    def test_to_point(self):
        count_data = 123
        timestamp = datetime(1970, 1, 1)
        agg = aggregation_data_module.CountAggregationData(count_data)
        converted_point = agg.to_point(timestamp)
        self.assertTrue(isinstance(converted_point, point.Point))
        self.assertTrue(isinstance(converted_point.value, value.ValueLong))
        self.assertEqual(converted_point.value.value, count_data)
        self.assertEqual(converted_point.timestamp, timestamp)


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

    def test_to_point(self):
        val = 1.2
        timestamp = datetime(1970, 1, 1)
        agg = aggregation_data_module.LastValueAggregationData(val)
        converted_point = agg.to_point(timestamp)
        self.assertTrue(isinstance(converted_point, point.Point))
        self.assertTrue(isinstance(converted_point.value, value.ValueDouble))
        self.assertEqual(converted_point.value.value, val)
        self.assertEqual(converted_point.timestamp, timestamp)


def exemplars_equal(stats_ex, metrics_ex):
    """Compare a stats exemplar to a metrics exemplar."""
    assert isinstance(stats_ex, aggregation_data_module.Exemplar)
    assert isinstance(metrics_ex, value.Exemplar)
    return (stats_ex.value == metrics_ex.value and
            stats_ex.timestamp == metrics_ex.timestamp and
            stats_ex.attachments == metrics_ex.attachments)


class TestDistributionAggregationData(unittest.TestCase):
    def test_constructor(self):
        mean_data = 1
        count_data = 0
        sum_of_sqd_deviations = mock.Mock()
        counts_per_bucket = [1, 1, 1]
        bounds = [1.0 / 2.0, 1]

        dist_agg_data = aggregation_data_module.DistributionAggregationData(
            mean_data=mean_data,
            count_data=count_data,
            sum_of_sqd_deviations=sum_of_sqd_deviations,
            counts_per_bucket=counts_per_bucket,
            bounds=bounds)

        self.assertEqual(1, dist_agg_data.mean_data)
        self.assertEqual(0, dist_agg_data.count_data)
        self.assertEqual(sum_of_sqd_deviations,
                         dist_agg_data.sum_of_sqd_deviations)
        self.assertEqual([1, 1, 1], dist_agg_data.counts_per_bucket)
        self.assertEqual([1.0 / 2.0, 1], dist_agg_data.bounds)

        self.assertIsNotNone(dist_agg_data.sum)
        self.assertEqual(0, dist_agg_data.variance)

    def test_init_bad_bucket_counts(self):
        # Check that len(counts_per_bucket) == len(bounds) + 1
        with self.assertRaises(AssertionError):
            aggregation_data_module.DistributionAggregationData(
                mean_data=mock.Mock(),
                count_data=mock.Mock(),
                sum_of_sqd_deviations=mock.Mock(),
                counts_per_bucket=[0, 0, 0],
                bounds=[1, 2, 3])

        # Check that counts aren't negative
        with self.assertRaises(AssertionError):
            aggregation_data_module.DistributionAggregationData(
                mean_data=mock.Mock(),
                count_data=mock.Mock(),
                sum_of_sqd_deviations=mock.Mock(),
                counts_per_bucket=[0, 2, -2, 0],
                bounds=[1, 2, 3])

        # And check that we don't throw given the right args
        aggregation_data_module.DistributionAggregationData(
            mean_data=mock.Mock(),
            count_data=mock.Mock(),
            sum_of_sqd_deviations=mock.Mock(),
            counts_per_bucket=[0, 0, 0, 0],
            bounds=[1, 2, 3])

    def test_init_bad_bounds(self):
        # Check that bounds are unique
        with self.assertRaises(AssertionError):
            aggregation_data_module.DistributionAggregationData(
                mean_data=mock.Mock(),
                count_data=mock.Mock(),
                sum_of_sqd_deviations=mock.Mock(),
                counts_per_bucket=[0, 0, 0, 0],
                bounds=[1, 2, 2])

        # Check that bounds are sorted
        with self.assertRaises(AssertionError):
            aggregation_data_module.DistributionAggregationData(
                mean_data=mock.Mock(),
                count_data=mock.Mock(),
                sum_of_sqd_deviations=mock.Mock(),
                counts_per_bucket=[0, 0, 0, 0],
                bounds=[1, 3, 2])

        # Check that all bounds are positive
        with self.assertRaises(AssertionError):
            aggregation_data_module.DistributionAggregationData(
                mean_data=mock.Mock(),
                count_data=mock.Mock(),
                sum_of_sqd_deviations=mock.Mock(),
                counts_per_bucket=[0, 0, 0, 0],
                bounds=[-1, 1, 2])

    def test_init_bad_exemplars(self):
        # Check that we don't allow exemplars without bounds
        with self.assertRaises(ValueError):
            aggregation_data_module.DistributionAggregationData(
                mean_data=mock.Mock(),
                count_data=mock.Mock(),
                sum_of_sqd_deviations=mock.Mock(),
                counts_per_bucket=mock.Mock(),
                bounds=None,
                exemplars=[mock.Mock()])

        # Check that the exemplar count matches the bucket count
        with self.assertRaises(ValueError):
            aggregation_data_module.DistributionAggregationData(
                mean_data=mock.Mock(),
                count_data=mock.Mock(),
                sum_of_sqd_deviations=mock.Mock(),
                counts_per_bucket=mock.Mock(),
                bounds=[0, 1],
                exemplars=[mock.Mock(), mock.Mock()])

    def test_constructor_with_exemplar(self):
        timestamp = time.time()
        attachments = {"One": "one", "Two": "two"}
        exemplars = [
            aggregation_data_module.Exemplar(.07, timestamp, attachments),
            aggregation_data_module.Exemplar(.7, timestamp, attachments),
            aggregation_data_module.Exemplar(7, timestamp, attachments)
        ]
        mean_data = 2.59
        count_data = 3
        sum_of_sqd_deviations = mock.Mock()
        counts_per_bucket = [1, 1, 1]
        bounds = [1.0 / 2.0, 1]

        dist_agg_data = aggregation_data_module.DistributionAggregationData(
            mean_data=mean_data,
            count_data=count_data,
            sum_of_sqd_deviations=sum_of_sqd_deviations,
            exemplars=exemplars,
            counts_per_bucket=counts_per_bucket,
            bounds=bounds)

        self.assertEqual(dist_agg_data.mean_data, mean_data)
        self.assertEqual(dist_agg_data.count_data, count_data)
        self.assertEqual(dist_agg_data.sum_of_sqd_deviations,
                         sum_of_sqd_deviations)
        self.assertEqual(dist_agg_data.counts_per_bucket, counts_per_bucket)
        self.assertEqual(dist_agg_data.bounds, bounds)
        self.assertEqual(dist_agg_data.sum, mean_data * count_data)
        for ii, ex in enumerate(exemplars):
            self.assertEqual(dist_agg_data.exemplars[ii], ex)

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
        sum_of_sqd_deviations = mock.Mock()
        counts_per_bucket = [1, 1, 1]
        bounds = [1.0 / 2.0, 1]
        dist_agg_data = aggregation_data_module.DistributionAggregationData(
            mean_data=mean_data,
            count_data=count_data,
            sum_of_sqd_deviations=sum_of_sqd_deviations,
            counts_per_bucket=counts_per_bucket,
            bounds=bounds)
        self.assertEqual(0, dist_agg_data.variance)

        count_data = 2
        sum_of_sqd_deviations = 2
        dist_agg_data = aggregation_data_module.DistributionAggregationData(
            mean_data=mean_data,
            count_data=count_data,
            sum_of_sqd_deviations=sum_of_sqd_deviations,
            counts_per_bucket=counts_per_bucket,
            bounds=bounds)
        self.assertEqual(2.0, dist_agg_data.variance)

    def test_add_sample(self):
        mean_data = 1.0
        count_data = 0
        sum_of_sqd_deviations = 2
        counts_per_bucket = [1, 1, 1, 1]
        bounds = [0.5, 1, 1.5]

        value = 3

        dist_agg_data = aggregation_data_module.DistributionAggregationData(
            mean_data=mean_data,
            count_data=count_data,
            sum_of_sqd_deviations=sum_of_sqd_deviations,
            counts_per_bucket=counts_per_bucket,
            bounds=bounds)

        dist_agg_data.add_sample(value, None, None)
        self.assertEqual(1, dist_agg_data.count_data)
        self.assertEqual(value, dist_agg_data.mean_data)

        count_data = 1
        dist_agg_data = aggregation_data_module.DistributionAggregationData(
            mean_data=mean_data,
            count_data=count_data,
            sum_of_sqd_deviations=sum_of_sqd_deviations,
            counts_per_bucket=counts_per_bucket,
            bounds=bounds)

        dist_agg_data.add_sample(value, None, None)
        self.assertEqual(2, dist_agg_data.count_data)
        self.assertEqual(2.0, dist_agg_data.mean_data)
        self.assertEqual(4.0, dist_agg_data.sum_of_sqd_deviations)
        self.assertIsNot(0, dist_agg_data.count_data)

    def test_add_sample_attachment(self):
        mean_data = 1.0
        count_data = 1
        sum_of_sqd_deviations = 2
        counts_per_bucket = [1, 1, 1, 1]
        bounds = [0.5, 1, 1.5]

        value = 3
        timestamp = time.time()
        attachments = {"One": "one", "Two": "two"}
        exemplar_1 = aggregation_data_module.Exemplar(4, timestamp,
                                                      attachments)

        dist_agg_data = aggregation_data_module.DistributionAggregationData(
            mean_data=mean_data,
            count_data=count_data,
            sum_of_sqd_deviations=sum_of_sqd_deviations,
            counts_per_bucket=counts_per_bucket,
            bounds=bounds,
            exemplars=[None, None, None, exemplar_1])

        self.assertEqual(dist_agg_data.exemplars[3], exemplar_1)

        dist_agg_data.add_sample(value, timestamp, attachments)
        self.assertEqual(2, dist_agg_data.count_data)
        self.assertEqual(2.0, dist_agg_data.mean_data)
        # Check that adding a sample overwrites the bucket's exemplar
        self.assertNotEqual(dist_agg_data.exemplars[3], exemplar_1)
        self.assertEqual(dist_agg_data.exemplars[3].value, 3)
        self.assertEqual(dist_agg_data.exemplars[3].attachments, attachments)

        count_data = 4
        dist_agg_data = aggregation_data_module.DistributionAggregationData(
            mean_data=mean_data,
            count_data=count_data,
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
        sum_of_sqd_deviations = mock.Mock()
        counts_per_bucket = [0]
        bounds = []

        value = 1

        dist_agg_data = aggregation_data_module.DistributionAggregationData(
            mean_data=mean_data,
            count_data=count_data,
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
            sum_of_sqd_deviations=sum_of_sqd_deviations,
            counts_per_bucket=counts_per_bucket,
            bounds=bounds)

        dist_agg_data.increment_bucket_count(value=value)
        self.assertEqual([1, 2, 1], dist_agg_data.counts_per_bucket)

        bounds = [1.0 / 4.0, 1.0 / 2.0]

        dist_agg_data = aggregation_data_module.DistributionAggregationData(
            mean_data=mean_data,
            count_data=count_data,
            sum_of_sqd_deviations=sum_of_sqd_deviations,
            counts_per_bucket=counts_per_bucket,
            bounds=bounds)

        dist_agg_data.increment_bucket_count(value=value)
        self.assertEqual([1, 2, 2], dist_agg_data.counts_per_bucket)

    def test_to_point(self):
        timestamp = datetime(1970, 1, 1)
        ex_9 = aggregation_data_module.Exemplar(
            9, timestamp, {'trace_id': 'dead', 'span_id': 'beef'}
        )
        ex_99 = aggregation_data_module.Exemplar(
            99, timestamp, {'trace_id': 'dead', 'span_id': 'bef0'}
        )
        dist_agg_data = aggregation_data_module.DistributionAggregationData(
            mean_data=50,
            count_data=99,
            sum_of_sqd_deviations=80850.0,
            counts_per_bucket=[0, 9, 90, 0],
            bounds=[1, 10, 100],
            exemplars=[None, ex_9, ex_99, None],
        )
        converted_point = dist_agg_data.to_point(timestamp)
        self.assertTrue(isinstance(converted_point.value,
                                   value.ValueDistribution))
        self.assertEqual(converted_point.value.count, 99)
        self.assertEqual(converted_point.value.sum, 4950)
        self.assertEqual(converted_point.value.sum_of_squared_deviation,
                         80850.0)
        self.assertEqual([bb.count for bb in converted_point.value.buckets],
                         [0, 9, 90, 0])
        self.assertEqual(converted_point.value.bucket_options.type_.bounds,
                         [1, 10, 100])
        self.assertTrue(
            exemplars_equal(
                ex_9,
                converted_point.value.buckets[1].exemplar))
        self.assertTrue(
            exemplars_equal(
                ex_99,
                converted_point.value.buckets[2].exemplar))

    def test_to_point_no_histogram(self):
        timestamp = datetime(1970, 1, 1)
        dist_agg_data = aggregation_data_module.DistributionAggregationData(
            mean_data=50,
            count_data=99,
            sum_of_sqd_deviations=80850.0,
        )
        converted_point = dist_agg_data.to_point(timestamp)
        self.assertTrue(isinstance(converted_point.value,
                                   value.ValueDistribution))
        self.assertEqual(converted_point.value.count, 99)
        self.assertEqual(converted_point.value.sum, 4950)
        self.assertEqual(converted_point.value.sum_of_squared_deviation,
                         80850.0)
        self.assertIsNone(converted_point.value.buckets)
        self.assertIsNone(converted_point.value.bucket_options._type)
