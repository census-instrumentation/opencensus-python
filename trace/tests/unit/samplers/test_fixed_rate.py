# Copyright 2017, OpenCensus Authors
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

from opencensus.trace.samplers import fixed_rate


class TestFixedRateSampler(unittest.TestCase):

    def test_constructor_invalid(self):
        with self.assertRaises(ValueError):
            fixed_rate.FixedRateSampler(rate=2)

    def test_constructor_valid(self):
        rate = 0.5
        sampler = fixed_rate.FixedRateSampler(rate=rate)

        self.assertEqual(sampler.rate, rate)

    def test_should_sample_smaller(self):
        sampler = fixed_rate.FixedRateSampler(rate=1)
        should_sample = sampler.should_sample

        self.assertTrue(should_sample)

    def test_should_sample_greater(self):
        sampler = fixed_rate.FixedRateSampler(rate=0)
        should_sample = sampler.should_sample

        self.assertFalse(should_sample)
