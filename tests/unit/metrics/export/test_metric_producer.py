# Copyright 2019, OpenCensus Authors
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

try:
    from mock import Mock
except ImportError:
    from unittest.mock import Mock

import unittest

from opencensus.metrics.export import metric_producer


class TestMetricProducerManager(unittest.TestCase):
    def test_init(self):
        mpm1 = metric_producer.MetricProducerManager()
        self.assertEqual(mpm1.metric_producers, set())

        mock_mp = Mock()
        mpm2 = metric_producer.MetricProducerManager([mock_mp])
        self.assertEqual(mpm2.metric_producers, set([mock_mp]))

    def test_add_remove(self):
        mpm = metric_producer.MetricProducerManager()
        self.assertEqual(mpm.metric_producers, set())

        with self.assertRaises(ValueError):
            mpm.add(None)
        mock_mp = Mock()
        mpm.add(mock_mp)
        self.assertEqual(mpm.metric_producers, set([mock_mp]))
        mpm.add(mock_mp)
        self.assertEqual(mpm.metric_producers, set([mock_mp]))

        with self.assertRaises(ValueError):
            mpm.remove(None)
        another_mock_mp = Mock()
        mpm.remove(another_mock_mp)
        self.assertEqual(mpm.metric_producers, set([mock_mp]))
        mpm.remove(mock_mp)
        self.assertEqual(mpm.metric_producers, set())

    def test_get_all(self):
        mp1 = Mock()
        mp2 = Mock()
        mpm = metric_producer.MetricProducerManager([mp1, mp2])
        got = mpm.get_all()
        mpm.remove(mp1)
        self.assertIn(mp1, got)
        self.assertIn(mp2, got)
