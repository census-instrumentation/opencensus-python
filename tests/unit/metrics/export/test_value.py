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
        double_value = value_module.ValueDouble(-34.56)

        self.assertIsNotNone(double_value)
        self.assertIsInstance(double_value, value_module.ValueDouble)
        self.assertEqual(double_value.value, -34.56)

    def test_create_long_value(self):
        long_value = value_module.ValueLong(123456789)

        self.assertIsNotNone(long_value)
        self.assertIsInstance(long_value, value_module.ValueLong)
        self.assertEqual(long_value.value, 123456789)

    def test_create_summary_value(self):
        value_at_percentile = [summary_module.ValueAtPercentile(99.5, 10.2)]
        snapshot = summary_module.Snapshot(10, 87.07, value_at_percentile)
        summary = summary_module.Summary(10, 6.6, snapshot)

        summary_value = value_module.ValueSummary(summary)

        self.assertIsNotNone(summary_value)
        self.assertIsInstance(summary_value, value_module.ValueSummary)
        self.assertEqual(summary_value.value, summary)


VD_COUNT = 100
VD_SUM = 1000.0
VD_SUM_OF_SQUARED_DEVIATION = 10.0
BOUNDS = list(range(1, 10))
BUCKET_OPTIONS = value_module.BucketOptions(value_module.Explicit(BOUNDS))
BUCKETS = [value_module.Bucket(10, None) for ii in range(10)]


class TestValueDistribution(unittest.TestCase):
    def test_init(self):
        distribution = value_module.ValueDistribution(
            VD_COUNT, VD_SUM, VD_SUM_OF_SQUARED_DEVIATION, BUCKET_OPTIONS,
            BUCKETS)
        self.assertEqual(distribution.count, VD_COUNT)
        self.assertEqual(distribution.sum, VD_SUM)
        self.assertEqual(distribution.sum_of_squared_deviation,
                         VD_SUM_OF_SQUARED_DEVIATION)
        self.assertEqual(distribution.bucket_options, BUCKET_OPTIONS)
        self.assertEqual(distribution.bucket_options.type_.bounds, BOUNDS)
        self.assertEqual(distribution.buckets, BUCKETS)

    def test_init_no_histogram(self):
        distribution = value_module.ValueDistribution(
            VD_COUNT, VD_SUM, VD_SUM_OF_SQUARED_DEVIATION,
            value_module.BucketOptions(), None)
        self.assertEqual(distribution.count, VD_COUNT)
        self.assertEqual(distribution.sum, VD_SUM)
        self.assertEqual(distribution.sum_of_squared_deviation,
                         VD_SUM_OF_SQUARED_DEVIATION)
        self.assertIsNone(distribution.bucket_options.type_)
        self.assertEqual(distribution.buckets, None)

    def test_init_bad_args(self):
        value_module.ValueDistribution(VD_COUNT, VD_SUM,
                                       VD_SUM_OF_SQUARED_DEVIATION,
                                       BUCKET_OPTIONS, BUCKETS)

        with self.assertRaises(ValueError):
            value_module.ValueDistribution(-1, VD_SUM,
                                           VD_SUM_OF_SQUARED_DEVIATION,
                                           BUCKET_OPTIONS, BUCKETS)

        with self.assertRaises(ValueError):
            value_module.ValueDistribution(0, VD_SUM,
                                           VD_SUM_OF_SQUARED_DEVIATION,
                                           BUCKET_OPTIONS, BUCKETS)

        with self.assertRaises(ValueError):
            value_module.ValueDistribution(0, 0, VD_SUM_OF_SQUARED_DEVIATION,
                                           BUCKET_OPTIONS, BUCKETS)

        with self.assertRaises(ValueError):
            value_module.ValueDistribution(
                VD_COUNT, VD_SUM, VD_SUM_OF_SQUARED_DEVIATION, None, BUCKETS)

        with self.assertRaises(ValueError):
            value_module.ValueDistribution(0, 0, 0, BUCKET_OPTIONS, BUCKETS)

        with self.assertRaises(ValueError):
            value_module.ValueDistribution(VD_COUNT - 1, VD_SUM,
                                           VD_SUM_OF_SQUARED_DEVIATION,
                                           BUCKET_OPTIONS, BUCKETS)

        with self.assertRaises(ValueError):
            value_module.ValueDistribution(VD_COUNT, VD_SUM,
                                           VD_SUM_OF_SQUARED_DEVIATION,
                                           value_module.BucketOptions(),
                                           BUCKETS)

        with self.assertRaises(ValueError):
            value_module.ValueDistribution(VD_COUNT, VD_SUM,
                                           VD_SUM_OF_SQUARED_DEVIATION,
                                           BUCKET_OPTIONS, BUCKETS[:-1])

    def test_init_empty_buckets_null_bucket_options(self):
        pass


EX_VALUE = 1.0
EX_TIMESTAMP = '2018-10-06T17:57:57.936475Z'
EX_ATTACHMENTS = {'attach': 'ments'}


class TestExemplar(unittest.TestCase):
    def test_init(self):
        exemplar = value_module.Exemplar(EX_VALUE, EX_TIMESTAMP,
                                         EX_ATTACHMENTS)
        self.assertEqual(exemplar.value, EX_VALUE)
        self.assertEqual(exemplar.timestamp, EX_TIMESTAMP)
        self.assertEqual(exemplar.attachments, EX_ATTACHMENTS)


class TestBucket(unittest.TestCase):
    def setUp(self):
        self.exemplar = value_module.Exemplar(EX_VALUE, EX_TIMESTAMP,
                                              EX_ATTACHMENTS)

    def test_init(self):
        bucket = value_module.Bucket(1, self.exemplar)
        self.assertEqual(bucket.count, 1)
        self.assertEqual(bucket.exemplar, self.exemplar)


class TestExplicit(unittest.TestCase):
    def test_init(self):
        bounds = [1, 2]
        explicit = value_module.Explicit(bounds)
        self.assertEqual(explicit.bounds, bounds)

    def test_bad_init(self):
        with self.assertRaises(ValueError):
            value_module.Explicit(None)
        with self.assertRaises(ValueError):
            value_module.Explicit([])
        with self.assertRaises(ValueError):
            value_module.Explicit([-1, 1, 2])
        with self.assertRaises(ValueError):
            value_module.Explicit([0, 1, 2])
        with self.assertRaises(ValueError):
            value_module.Explicit([1, 1])
        with self.assertRaises(ValueError):
            value_module.Explicit([2, 1])
