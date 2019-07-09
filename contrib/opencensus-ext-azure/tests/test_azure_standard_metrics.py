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

import inspect
import unittest

from opencensus.ext.azure.metrics_exporter import standard_metrics
from opencensus.metrics.export.gauge import Registry


class TestStandardMetrics(unittest.TestCase):
    def test_producer_ctor(self):
        producer = standard_metrics.AzureStandardMetricsProducer()

        attributes = inspect.getmembers(
            standard_metrics.StandardMetricsType,
            lambda a: not(inspect.isroutine(a)))
        types = [a for a in attributes
                 if not(a[0].startswith('__') and
                        a[0].endswith('__'))]
        self.assertEquals(len(producer.metrics), len(types))

    def test_available_memory_register(self):
        registry = Registry()
        metric = standard_metrics.AvailableMemoryStandardMetric()
        metric.register(registry)
        available_memory_type = standard_metrics\
            .StandardMetricsType.AVAILABLE_MEMORY

        self.assertEqual(len(registry.gauges), 1)
        self.assertIsNotNone(registry.gauges[available_memory_type])
