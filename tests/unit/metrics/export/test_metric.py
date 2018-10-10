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

from opencensus.metrics.export.metric import Metric
from opencensus.metrics.export.time_series import TimeSeries
from opencensus.metrics.export.metric_descriptor import MetricDescriptor
from opencensus.metrics.export.metric_descriptor import MetricDescriptorType


class TestMetric(unittest.TestCase):
    def test_init(self):

        # Check for required arg errors
        with self.assertRaises(ValueError):
            Metric(Mock(), None)
        with self.assertRaises(ValueError):
            Metric(Mock(), None)

        mock_time_series = Mock(spec=TimeSeries)
        mock_time_series.check_points_type.return_value = True

        mock_descriptor = Mock(spec=MetricDescriptor)
        mock_descriptor.type = MetricDescriptorType.GAUGE_INT64

        metric = Metric([mock_time_series], mock_descriptor)
        self.assertEqual(metric.time_series, [mock_time_series])
        self.assertEqual(metric.descriptor, mock_descriptor)

    def test_init_wrong_ts_type(self):
        mock_descriptor = Mock(spec=MetricDescriptor)
        mock_descriptor.type = MetricDescriptorType.GAUGE_INT64

        mock_time_series1 = Mock(spec=TimeSeries)
        mock_time_series1.check_points_type.return_value = True

        mock_time_series2 = Mock(spec=TimeSeries)
        mock_time_series2.check_points_type.return_value = False

        with self.assertRaises(ValueError):
            Metric([mock_time_series1, mock_time_series2], mock_descriptor)
