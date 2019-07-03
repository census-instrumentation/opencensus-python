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

import mock
import unittest

from opencensus.ext.azure.metrics_exporter.standard_metrics import StandardMetricsRecorder
from opencensus.ext.azure.metrics_exporter.standard_metrics import StandardMetricsType
from opencensus.stats import execution_context
from opencensus.stats import stats as stats_module


class TestStandardMetrics(unittest.TestCase):
    def setUp(self):
        execution_context.set_measure_to_view_map({})
        stats_module.stats = stats_module._Stats()

    def test_constructor_and_setup(self):
        standard_metrics = StandardMetricsRecorder()
        measurement_map = standard_metrics.measurement_map
        measure_map = standard_metrics.measure_map

        self.assertIsNotNone(measurement_map)
        self.assertEqual(len(measurement_map._measurement_map), 0)
        self.assertEqual(len(measure_map), 1)
        self.assertIsNotNone(measure_map[StandardMetricsType.AVAILABLE_MEMORY])

    def test_record_standard_metrics(self):
        with mock.patch('psutil.virtual_memory') as psutil_mock:
            type(psutil_mock.return_value).available = mock.PropertyMock(
                return_value=1.0)
            standard_metrics = StandardMetricsRecorder()
            standard_metrics.record_standard_metrics()

            self.assertIsNotNone(standard_metrics.measure_map[StandardMetricsType.AVAILABLE_MEMORY])
            self.assertEqual(len(standard_metrics.measurement_map._measurement_map), 1)
            self.assertEqual(standard_metrics.measurement_map._measurement_map[standard_metrics.measure_map[StandardMetricsType.AVAILABLE_MEMORY]], 1.0)


