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

from opencensus.stats import bucket_boundaries as bucket_boundaries_module


class TestBucketBoundaries(unittest.TestCase):
    def test_constructor_defaults(self):
        bucket_boundaries = bucket_boundaries_module.BucketBoundaries()
        self.assertEqual([], bucket_boundaries.boundaries)

    def test_constructor_explicit(self):
        boundaries = [1 / 4]
        bucket_boundaries = bucket_boundaries_module.BucketBoundaries(
            boundaries=boundaries)
        self.assertTrue(bucket_boundaries.is_valid_boundaries(boundaries))
        self.assertEqual(boundaries, bucket_boundaries.boundaries)

    def test_is_valid_boundaries(self):
        boundaries = [0, 1 / 4, 1 / 2]
        bucket_boundaries = bucket_boundaries_module.BucketBoundaries(
            boundaries=boundaries)
        self.assertTrue(
            bucket_boundaries.is_valid_boundaries(boundaries=boundaries))

        boundaries = [2, 1, 0]
        bucket_boundaries = bucket_boundaries_module.BucketBoundaries(
            boundaries=boundaries)
        self.assertFalse(
            bucket_boundaries.is_valid_boundaries(boundaries=boundaries))

        boundaries = None
        bucket_boundaries = bucket_boundaries_module.BucketBoundaries(
            boundaries=boundaries)
        self.assertFalse(
            bucket_boundaries.is_valid_boundaries(boundaries=boundaries))
