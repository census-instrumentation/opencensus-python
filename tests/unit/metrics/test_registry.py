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

from opencensus.metrics import registry


class TestRegistry(unittest.TestCase):
    def test_add_gauge(self):
        reg = registry.Registry()

        with self.assertRaises(ValueError):
            reg.add_gauge(None)

        gauge1 = Mock()
        gauge1.descriptor.name = 'gauge1'
        gauge2 = Mock()
        gauge2.descriptor.name = 'gauge2'

        reg.add_gauge(gauge1)
        self.assertDictEqual(reg.gauges, {'gauge1': gauge1})
        reg.add_gauge(gauge2)
        self.assertDictEqual(reg.gauges, {'gauge1': gauge1, 'gauge2': gauge2})

        with self.assertRaises(ValueError):
            reg.add_gauge(gauge2)

    def test_get_metrics(self):
        reg = registry.Registry()

        with self.assertRaises(ValueError):
            reg.add_gauge(None)

        gauge1 = Mock()
        gauge1.descriptor.name = 'gauge1'
        metric1 = Mock()
        gauge1.get_metric.return_value = metric1

        gauge2 = Mock()
        gauge2.descriptor.name = 'gauge2'
        metric2 = Mock()
        gauge2.get_metric.return_value = metric2

        self.assertSetEqual(reg.get_metrics(), set())
        reg.add_gauge(gauge1)
        self.assertSetEqual(reg.get_metrics(), {metric1})
        reg.add_gauge(gauge2)
        self.assertSetEqual(reg.get_metrics(), {metric1, metric2})
