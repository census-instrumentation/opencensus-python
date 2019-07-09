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
import mock
import unittest

from opencensus.metrics.export import standard_metrics
from opencensus.metrics.export.gauge import DerivedLongGauge

class TestStandardMetrics(unittest.TestCase):
    def test_producer_register(self):
        producer = standard_metrics.StandardMetricsProducer()
        metric = standard_metrics.BaseStandardMetric()
        metric.register = mock.Mock()
        metrics = [metric]
        producer.register_metrics(metrics)

        metric.register.assert_called_once()

    def test_producer_get_metrics(self):
        test_gauge = DerivedLongGauge('test gauge',
            'test',
            'test',
            [])
        func = lambda x:(1)
        test_gauge.create_default_time_series(func)
        producer = standard_metrics.StandardMetricsProducer()
        producer.gauges[test_gauge.descriptor.name] = test_gauge
        metrics = []

        for metric in producer.get_metrics():
            metrics.append(metric)

        self.assertEqual(len(metrics), 1)
