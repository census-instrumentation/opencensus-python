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

import mock

from opencensus.trace import samplers


class TestProbabilitySampler(unittest.TestCase):
    def test_constructor_invalid(self):
        with self.assertRaises(ValueError):
            samplers.ProbabilitySampler(rate=2)

    def test_constructor_valid(self):
        rate = 0.8
        sampler = samplers.ProbabilitySampler(rate=rate)

        self.assertEqual(sampler.rate, rate)

    def test_constructor_default(self):
        sampler = samplers.ProbabilitySampler()
        self.assertEqual(sampler.rate, samplers.DEFAULT_SAMPLING_RATE)

    def test_should_sample_smaller(self):
        trace_id = 'f8739df974a4481f98748cd92b27177d'
        mock_context = mock.Mock()
        mock_context.trace_id = trace_id
        mock_context.trace_options.get_enabled.return_value = False

        sampler = samplers.ProbabilitySampler(rate=1)
        self.assertTrue(sampler.should_sample(mock_context))

    def test_should_sample_greater(self):
        trace_id = 'f8739df974a4481f98748cd92b27177d'
        mock_context = mock.Mock()
        mock_context.trace_id = trace_id
        mock_context.trace_options.get_enabled.return_value = False

        sampler = samplers.ProbabilitySampler()
        self.assertFalse(sampler.should_sample(mock_context))

    def test_should_sample_low_traceid(self):
        trace_id = '000000000000000000068db8bac710cb'
        mock_context = mock.Mock()
        mock_context.trace_id = trace_id
        mock_context.trace_options.get_enabled.return_value = False

        sampler = samplers.ProbabilitySampler()
        self.assertTrue(sampler.should_sample(mock_context))

        # Check that we only check the last 8 bytes
        trace_id2 = 'ffffffffffffffff00068db8bac710cb'
        mock_context.trace_id = trace_id2
        self.assertTrue(sampler.should_sample(mock_context))

    def test_should_sample_high_traceid(self):
        trace_id = '000000000000000000068db8bac710cc'
        mock_context = mock.Mock()
        mock_context.trace_id = trace_id
        mock_context.trace_options.get_enabled.return_value = False

        sampler = samplers.ProbabilitySampler()
        self.assertFalse(sampler.should_sample(mock_context))

    def test_should_sample_short_circuit(self):
        trace_id = 'ffffffffffffffffffffffffffffffff'
        mock_context = mock.Mock()
        mock_context.trace_id = trace_id
        mock_context.trace_options.get_enabled.return_value = True

        sampler = samplers.ProbabilitySampler()
        self.assertTrue(sampler.should_sample(mock_context))
