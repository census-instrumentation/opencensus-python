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

import datetime
import unittest

from opencensus.metrics.export import metric_descriptor
from opencensus.metrics.export import point
from opencensus.metrics.export import value
from opencensus.stats import aggregation
from opencensus.stats import aggregation_data
from opencensus.stats import measure
from opencensus.stats import metric_utils
from opencensus.stats import view
from opencensus.stats import view_data
from opencensus.tags import tag_key
from opencensus.tags import tag_value


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

    def do_test_view_data_to_metric(self, aggregation_type, aggregation_class,
                                    value_type, metric_descriptor_type):
        """Test that ViewDatas are converted correctly into Metrics.

        This test doesn't check that the various aggregation data `to_point`
        methods handle the point conversion correctly, just that converted
        Point is included in the Metric, and the metric has the expected
        structure, descriptor, and labels.
        """
        start_time = datetime.datetime(2019, 1, 25, 11, 12, 13)
        current_time = datetime.datetime(2019, 1, 25, 12, 13, 14)

        mock_measure = mock.Mock(spec=measure.MeasureFloat)
        mock_aggregation = mock.Mock(spec=aggregation_class)
        mock_aggregation.aggregation_type = aggregation_type

        vv = view.View(
            name=mock.Mock(),
            description=mock.Mock(),
            columns=[tag_key.TagKey('k1'), tag_key.TagKey('k2')],
            measure=mock_measure,
            aggregation=mock_aggregation)

        vd = mock.Mock(spec=view_data.ViewData)
        vd.view = vv
        vd.start_time = start_time

        mock_point = mock.Mock(spec=point.Point)
        mock_point.value = mock.Mock(spec=value_type)

        mock_agg = mock.Mock(spec=aggregation_data.SumAggregationDataFloat)
        mock_agg.to_point.return_value = mock_point

        vd.tag_value_aggregation_data_map = {
            (tag_value.TagValue('v1'), tag_value.TagValue('v2')): mock_agg
        }

        metric = metric_utils.view_data_to_metric(vd, current_time)
        mock_agg.to_point.assert_called_once_with(current_time)

        self.assertEqual(metric.descriptor.name, vv.name)
        self.assertEqual(metric.descriptor.description, vv.description)
        self.assertEqual(metric.descriptor.unit, vv.measure.unit)
        self.assertEqual(metric.descriptor.type, metric_descriptor_type)
        self.assertListEqual(
            [lk.key for lk in metric.descriptor.label_keys],
            ['k1', 'k2'])

        self.assertEqual(len(metric.time_series), 1)
        [ts] = metric.time_series
        self.assertEqual(ts.start_timestamp, start_time)
        self.assertListEqual(
            [lv.value for lv in ts.label_values],
            ['v1', 'v2'])
        self.assertEqual(len(ts.points), 1)
        [pt] = ts.points
        self.assertEqual(pt, mock_point)

    def test_view_data_to_metric(self):
        args_list = [
            [
                aggregation.Type.SUM,
                aggregation.SumAggregation,
                value.ValueDouble,
                metric_descriptor.MetricDescriptorType.CUMULATIVE_DOUBLE
            ],
            [
                aggregation.Type.COUNT,
                aggregation.CountAggregation,
                value.ValueLong,
                metric_descriptor.MetricDescriptorType.CUMULATIVE_INT64
            ],
            [
                aggregation.Type.DISTRIBUTION,
                aggregation.DistributionAggregation,
                value.ValueDistribution,
                metric_descriptor.MetricDescriptorType.CUMULATIVE_DISTRIBUTION
            ]
        ]
        for args in args_list:
            self.do_test_view_data_to_metric(*args)

    def test_convert_view_without_labels(self):
        mock_measure = mock.Mock(spec=measure.MeasureFloat)
        mock_aggregation = mock.Mock(spec=aggregation.DistributionAggregation)
        mock_aggregation.aggregation_type = aggregation.Type.DISTRIBUTION

        vd = mock.Mock(spec=view_data.ViewData)
        vd.view = view.View(
            name=mock.Mock(),
            description=mock.Mock(),
            columns=[],
            measure=mock_measure,
            aggregation=mock_aggregation)
        vd.start_time = '2019-04-11T22:33:44.555555Z'

        mock_point = mock.Mock(spec=point.Point)
        mock_point.value = mock.Mock(spec=value.ValueDistribution)

        mock_agg = mock.Mock(spec=aggregation_data.SumAggregationDataFloat)
        mock_agg.to_point.return_value = mock_point

        vd.tag_value_aggregation_data_map = {tuple(): mock_agg}

        current_time = '2019-04-11T22:33:55.666666Z'
        metric = metric_utils.view_data_to_metric(vd, current_time)

        self.assertEqual(metric.descriptor.label_keys, [])
        self.assertEqual(len(metric.time_series), 1)
        [ts] = metric.time_series
        self.assertEqual(ts.label_values, [])
        self.assertEqual(len(ts.points), 1)
        [pt] = ts.points
        self.assertEqual(pt, mock_point)
