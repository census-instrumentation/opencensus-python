# -*- coding: utf-8 -*-

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

from opencensus.metrics.export.metric_descriptor import MetricDescriptorType
from opencensus.metrics.export.point import Point
from opencensus.metrics.export.time_series import TimeSeries
from opencensus.metrics.export.value import Value
from opencensus.metrics.label_value import LabelValue

START_TIMESTAMP = '2018-10-09T22:33:44.012345Z'
LABEL_VALUE1 = LabelValue('value one')
LABEL_VALUE2 = LabelValue('价值二')
LABEL_VALUES = (LABEL_VALUE1, LABEL_VALUE2)
POINTS = (Point(Value.long_value(1), "2018-10-09T23:33:44.012345Z"),
          Point(Value.long_value(2), "2018-10-10T00:33:44.012345Z"),
          Point(Value.long_value(3), "2018-10-10T01:33:44.012345Z"),
          Point(Value.long_value(4), "2018-10-10T02:33:44.012345Z"),
          Point(Value.long_value(5), "2018-10-10T03:33:44.012345Z"))


class TestTimeSeries(unittest.TestCase):
    def test_init(self):
        time_series = TimeSeries(START_TIMESTAMP, LABEL_VALUES, POINTS)

        self.assertEqual(time_series.start_timestamp, START_TIMESTAMP)
        self.assertEqual(time_series.label_values, LABEL_VALUES)
        self.assertEqual(time_series.points, POINTS)

    def test_check_points_type(self):
        time_series = TimeSeries(START_TIMESTAMP, LABEL_VALUES, POINTS)
        self.assertTrue(
            time_series.check_points_type(MetricDescriptorType.GAUGE_INT64))

        bad_points = POINTS + (Point(
            Value.double_value(6.0), "2018-10-10T04:33:44.012345Z"), )
        bad_time_series = TimeSeries(START_TIMESTAMP, LABEL_VALUES, bad_points)

        self.assertFalse(
            bad_time_series.check_points_type(
                MetricDescriptorType.GAUGE_INT64))
        self.assertFalse(
            bad_time_series.check_points_type(
                MetricDescriptorType.GAUGE_DOUBLE))
