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
        return



