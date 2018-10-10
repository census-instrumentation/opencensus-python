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

from opencensus.metrics.export.time_series import TimeSeries
from opencensus.metrics.label_value import LabelValue

START_TIMESTAMP = '2018-10-09T22:33:44.012345Z'
LABEL_VALUE1 = LabelValue('value one')
LABEL_VALUE2 = LabelValue('价值二')
LABEL_VALUES = (LABEL_VALUE1, LABEL_VALUE2)
POINTS = ((1, "2018-10-09T23:33:44.012345Z"),
          (2, "2018-10-10T00:33:44.012345Z"),
          (3, "2018-10-10T01:33:44.012345Z"),
          (4, "2018-10-10T02:33:44.012345Z"),
          (5, "2018-10-10T03:33:44.012345Z"))


class TestTimeSeries(unittest.TestCase):

    def test_init(self):
        time_series = TimeSeries(START_TIMESTAMP, LABEL_VALUES, POINTS)

        self.assertEqual(time_series.start_timestamp, START_TIMESTAMP)
        self.assertEqual(time_series.label_values, LABEL_VALUES)
        self.assertEqual(time_series.points, POINTS)
