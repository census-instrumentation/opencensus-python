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

from opencensus.metrics.export import metric
from opencensus.metrics.export import metric_descriptor
from opencensus.metrics.export import time_series


class TestMetric(unittest.TestCase):
    def test_init(self):

        # Check for required arg errors
        with self.assertRaises(ValueError):
            metric.Metric(Mock(), None)
        with self.assertRaises(ValueError):
            metric.Metric(None, Mock())

        mock_time_series = Mock(spec=time_series.TimeSeries)
        mock_time_series.check_points_type.return_value = True

        mock_descriptor = Mock(spec=metric_descriptor.MetricDescriptor)
        mock_descriptor.type = (metric_descriptor
                                .MetricDescriptorType.GAUGE_INT64)

        mm = metric.Metric(mock_descriptor, [mock_time_series],)
        self.assertEqual(mm.time_series, [mock_time_series])
        self.assertEqual(mm.descriptor, mock_descriptor)

    def test_init_wrong_ts_type(self):
        mock_descriptor = Mock(spec=metric_descriptor.MetricDescriptor)

        mock_time_series1 = Mock(spec=time_series.TimeSeries)
        mock_time_series1.check_points_type.return_value = True

        mock_time_series2 = Mock(spec=time_series.TimeSeries)
        mock_time_series2.check_points_type.return_value = False

        for value_type in (
            metric_descriptor.MetricDescriptorType.GAUGE_INT64,
            metric_descriptor.MetricDescriptorType.CUMULATIVE_INT64,
            metric_descriptor.MetricDescriptorType.GAUGE_DOUBLE,
            metric_descriptor.MetricDescriptorType.CUMULATIVE_DOUBLE,
            metric_descriptor.MetricDescriptorType.GAUGE_DISTRIBUTION,
            metric_descriptor.MetricDescriptorType.CUMULATIVE_DISTRIBUTION,
            metric_descriptor.MetricDescriptorType.SUMMARY,
            10  # unspecified type
        ):
            with self.assertRaises(ValueError):
                mock_descriptor.type = value_type
                metric.Metric(mock_descriptor,
                              [mock_time_series1, mock_time_series2])

    def test_init_missing_start_timestamp(self):
        mock_ts = Mock(spec=time_series.TimeSeries)
        mock_ts.check_points_type.return_value = True
        mock_ts_no_start = Mock(spec=time_series.TimeSeries)
        mock_ts_no_start.start_timestamp = None
        mock_ts_no_start.check_points_type.return_value = True

        mock_descriptor_gauge = Mock(spec=metric_descriptor.MetricDescriptor)
        mock_descriptor_gauge.type = (
            metric_descriptor.MetricDescriptorType.GAUGE_INT64
        )
        mock_descriptor_cumulative = (
            Mock(spec=metric_descriptor.MetricDescriptor)
        )
        mock_descriptor_cumulative.type = (
            metric_descriptor.MetricDescriptorType.CUMULATIVE_INT64
        )

        (metric.Metric(mock_descriptor_gauge, [mock_ts])
         ._check_start_timestamp())
        (metric.Metric(mock_descriptor_cumulative, [mock_ts])
         ._check_start_timestamp())
        (metric.Metric(mock_descriptor_gauge, [mock_ts_no_start])
         ._check_start_timestamp())
        with self.assertRaises(ValueError):
            metric.Metric(mock_descriptor_cumulative,
                          [mock_ts_no_start])._check_start_timestamp()
