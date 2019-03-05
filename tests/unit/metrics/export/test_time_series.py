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

from opencensus.metrics import label_value
from opencensus.metrics.export import point
from opencensus.metrics.export import time_series
from opencensus.metrics.export import value

START_TIMESTAMP = '2018-10-09T22:33:44.012345Z'
LABEL_VALUE1 = label_value.LabelValue('value one')
LABEL_VALUE2 = label_value.LabelValue('价值二')
LABEL_VALUES = (LABEL_VALUE1, LABEL_VALUE2)
POINTS = (point.Point(
    value.ValueLong(1), "2018-10-09T23:33:44.012345Z"),
          point.Point(
              value.ValueLong(2), "2018-10-10T00:33:44.012345Z"),
          point.Point(
              value.ValueLong(3), "2018-10-10T01:33:44.012345Z"),
          point.Point(
              value.ValueLong(4), "2018-10-10T02:33:44.012345Z"),
          point.Point(
              value.ValueLong(5), "2018-10-10T03:33:44.012345Z"))


class TestTimeSeries(unittest.TestCase):
    def test_init(self):
        ts = time_series.TimeSeries(LABEL_VALUES, POINTS, START_TIMESTAMP)

        self.assertEqual(ts.start_timestamp, START_TIMESTAMP)
        self.assertEqual(ts.label_values, LABEL_VALUES)
        self.assertEqual(ts.points, POINTS)

    def test_init_invalid(self):
        time_series.TimeSeries(LABEL_VALUES, POINTS, None)
        with self.assertRaises(ValueError):
            time_series.TimeSeries(None, POINTS, START_TIMESTAMP)
        with self.assertRaises(ValueError):
            time_series.TimeSeries([], POINTS, START_TIMESTAMP)
        with self.assertRaises(ValueError):
            time_series.TimeSeries(LABEL_VALUES, None, START_TIMESTAMP)
        with self.assertRaises(ValueError):
            time_series.TimeSeries(LABEL_VALUES, [], START_TIMESTAMP)

    def test_check_points_type(self):
        ts = time_series.TimeSeries(LABEL_VALUES, POINTS, START_TIMESTAMP)
        self.assertTrue(ts.check_points_type(value.ValueLong))

        bad_points = POINTS + (point.Point(
            value.ValueDouble(6.0), "2018-10-10T04:33:44.012345Z"), )
        bad_time_series = time_series.TimeSeries(LABEL_VALUES, bad_points,
                                                 START_TIMESTAMP)

        self.assertFalse(bad_time_series.check_points_type(value.ValueLong))
        self.assertFalse(bad_time_series.check_points_type(value.ValueLong))
