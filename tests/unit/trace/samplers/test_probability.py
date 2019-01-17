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

from opencensus.trace.samplers import probability


class TestProbabilitySampler(unittest.TestCase):
    def test_constructor_invalid(self):
        with self.assertRaises(ValueError):
            probability.ProbabilitySampler(rate=2)

    def test_constructor_valid(self):
        rate = 0.8
        sampler = probability.ProbabilitySampler(rate=rate)

        self.assertEqual(sampler.rate, rate)

    def test_constructor_default(self):
        rate = 0.5
        sampler = probability.ProbabilitySampler()

        self.assertEqual(sampler.rate, rate)

    def test_should_sample_smaller(self):
        trace_id = 'f8739df974a4481f98748cd92b27177d'
        sampler = probability.ProbabilitySampler(rate=1)
        should_sample = sampler.should_sample(trace_id=trace_id)

        self.assertTrue(should_sample)

    def test_should_sample_greater(self):
        trace_id = 'f8739df974a4481f98748cd92b27177d'
        sampler = probability.ProbabilitySampler(rate=0)
        should_sample = sampler.should_sample(trace_id=trace_id)

        self.assertFalse(should_sample)

    def test_should_sample_trace_id_sampled(self):
        trace_id = '00000000000000000000000000000000'
        sampler = probability.ProbabilitySampler(rate=0.5)
        should_sample = sampler.should_sample(trace_id=trace_id)

        self.assertTrue(should_sample)

    def test_should_sample_trace_id_not_sampled(self):
        trace_id = 'ffffffffffffffffffffffffffffffff'
        sampler = probability.ProbabilitySampler(rate=0.5)
        should_sample = sampler.should_sample(trace_id=trace_id)

        self.assertFalse(should_sample)
