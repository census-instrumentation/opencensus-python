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
    import mock
except ImportError:
    from unittest import mock

import unittest

from opencensus.metrics.export import metric_descriptor
from opencensus.stats import aggregation
from opencensus.stats import measure
from opencensus.stats import metric_utils
from opencensus.stats import view


class TestMetricUtils(unittest.TestCase):
    def test_get_metric_type(self):
        measure_int = mock.Mock(spec=measure.MeasureInt)
        measure_float = mock.Mock(spec=measure.MeasureFloat)
        agg_sum = mock.Mock(spec=aggregation.SumAggregation)
        agg_sum.aggregation_type = aggregation.Type.SUM
        agg_count = mock.Mock(spec=aggregation.CountAggregation)
        agg_count.aggregation_type = aggregation.Type.COUNT
        agg_dist = mock.Mock(spec=aggregation.DistributionAggregation)
        agg_dist.aggregation_type = aggregation.Type.DISTRIBUTION
        agg_lv = mock.Mock(spec=aggregation.LastValueAggregation)
        agg_lv.aggregation_type = aggregation.Type.LASTVALUE

        view_to_metric_type = {
            (measure_int, agg_sum):
            metric_descriptor.MetricDescriptorType.CUMULATIVE_INT64,
            (measure_int, agg_count):
            metric_descriptor.MetricDescriptorType.CUMULATIVE_INT64,
            (measure_int, agg_dist):
            metric_descriptor.MetricDescriptorType.CUMULATIVE_DISTRIBUTION,
            (measure_int, agg_lv):
            metric_descriptor.MetricDescriptorType.GAUGE_INT64,
            (measure_float, agg_sum):
            metric_descriptor.MetricDescriptorType.CUMULATIVE_DOUBLE,
            (measure_float, agg_count):
            metric_descriptor.MetricDescriptorType.CUMULATIVE_INT64,
            (measure_float, agg_dist):
            metric_descriptor.MetricDescriptorType.CUMULATIVE_DISTRIBUTION,
            (measure_float, agg_lv):
            metric_descriptor.MetricDescriptorType.GAUGE_DOUBLE,
        }

        for (mm, ma), metric_type in view_to_metric_type.items():
            self.assertEqual(metric_utils.get_metric_type(mm, ma), metric_type)

    def test_get_metric_type_bad_aggregation(self):
        base_agg = mock.Mock(spec=aggregation.BaseAggregation)
        base_agg.aggregation_type = aggregation.Type.NONE
        with self.assertRaises(ValueError):
            metric_utils.get_metric_type(mock.Mock(), base_agg)

        bad_agg = mock.Mock(spec=aggregation.SumAggregation)
        bad_agg.aggregation_type = aggregation.Type.COUNT
        with self.assertRaises(AssertionError):
            metric_utils.get_metric_type(mock.Mock(), bad_agg)

    def test_get_metric_type_bad_measure(self):
        base_measure = mock.Mock(spec=measure.BaseMeasure)
        agg_sum = mock.Mock(spec=aggregation.SumAggregation)
        agg_sum.aggregation_type = aggregation.Type.SUM
        agg_lv = mock.Mock(spec=aggregation.LastValueAggregation)
        agg_lv.aggregation_type = aggregation.Type.LASTVALUE
        with self.assertRaises(ValueError):
            metric_utils.get_metric_type(base_measure, agg_sum)
        with self.assertRaises(ValueError):
            metric_utils.get_metric_type(base_measure, agg_lv)

    def test_get_metric_descriptor(self):
        mock_measure = mock.Mock(spec=measure.MeasureFloat)
        mock_agg = mock.Mock(spec=aggregation.SumAggregation)
        mock_agg.aggregation_type = aggregation.Type.SUM
        test_view = view.View("name", "description", ["tk1", "tk2"],
                              mock_measure, mock_agg)

        md = metric_utils.get_metric_descriptor(test_view)
        self.assertTrue(isinstance(md, metric_descriptor.MetricDescriptor))
        self.assertEqual(md.name, test_view.name)
        self.assertEqual(md.description, test_view.description)
        self.assertEqual(md.unit, test_view.measure.unit)
        self.assertEqual(
            md.type, metric_descriptor.MetricDescriptorType.CUMULATIVE_DOUBLE)
        self.assertTrue(
            all(lk.key == col
                for lk, col in zip(md.label_keys, test_view.columns)))
