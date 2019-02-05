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

try:
    from mock import Mock
except ImportError:
    from unittest.mock import Mock

import unittest

from opencensus.metrics.export import metric_descriptor
from opencensus.metrics.export import value
from opencensus.stats import aggregation
from opencensus.stats import measure
from opencensus.stats import stats as stats_module
from opencensus.stats import view
from opencensus.tags import tag_map


class TestStats(unittest.TestCase):
    def test_get_metrics(self):
        """Test that Stats converts recorded values into metrics."""

        stats = stats_module.Stats()

        # Check that metrics are empty before view registration
        initial_metrics = list(stats.get_metrics())
        self.assertEqual(initial_metrics, [])

        mock_measure = Mock(spec=measure.MeasureFloat)

        mock_md = Mock(spec=metric_descriptor.MetricDescriptor)
        mock_md.type =\
            metric_descriptor.MetricDescriptorType.CUMULATIVE_DISTRIBUTION

        mock_view = Mock(spec=view.View)
        mock_view.measure = mock_measure
        mock_view.get_metric_descriptor.return_value = mock_md
        mock_view.columns = ['k1']

        stats.view_manager.measure_to_view_map.register_view(mock_view, Mock())

        # Check that metrics are stil empty until we record
        empty_metrics = list(stats.get_metrics())
        self.assertEqual(empty_metrics, [])

        mm = stats.stats_recorder.new_measurement_map()
        mm._measurement_map = {mock_measure: 1.0}

        mock_view.aggregation = aggregation.DistributionAggregation()

        tm = tag_map.TagMap()
        tm.insert('k1', 'v1')
        mm.record(tm)

        metrics = list(stats.get_metrics())
        self.assertEqual(len(metrics), 1)
        [metric] = metrics
        self.assertEqual(len(metric.time_series), 1)
        [ts] = metric.time_series
        self.assertEqual(len(ts.points), 1)
        [point] = ts.points
        self.assertTrue(isinstance(point.value, value.ValueDistribution))
