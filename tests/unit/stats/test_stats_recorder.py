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
import mock
from opencensus.stats import stats_recorder as stats_recorder_module
from opencensus.stats.measurement_map import MeasurementMap
from opencensus.stats import execution_context


class TestStatsRecorder(unittest.TestCase):

    def test_constructor_defaults(self):
        execution_context.clear()
        self.assertEqual({}, execution_context.get_measure_to_view_map())

        stats_recorder = stats_recorder_module.StatsRecorder()

        self.assertIsNotNone(execution_context.get_measure_to_view_map())
        self.assertIs(stats_recorder.measure_to_view_map,
                      execution_context.get_measure_to_view_map())
        self.assertIsNotNone(stats_recorder.measure_to_view_map)

    def test_new_measurement_map(self):
        measure_to_view_map = mock.Mock
        stats_recorder = stats_recorder_module.StatsRecorder()
        measurement_map = stats_recorder.new_measurement_map()

        self.assertEqual(measurement_map.measurement_map, MeasurementMap(measure_to_view_map=measure_to_view_map).measurement_map)
