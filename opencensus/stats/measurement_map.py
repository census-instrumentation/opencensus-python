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

from datetime import datetime


class MeasurementMap(object):
    """Measurement Map is a map from Measures to measured values
    to be recorded at the same time

    :type measure_to_view_map: :class: '~opencensus.stats.measure_to_view_map.
                                        MeasureToViewMap'
    :param measure_to_view_map: the measure to view map that will store the
                                recorded stats with tags

    """
    def __init__(self, measure_to_view_map):
        self._measurement_map = {}
        self._measure_to_view_map = measure_to_view_map

    @property
    def measurement_map(self):
        """the current measurement map"""
        return self._measurement_map

    @property
    def measure_to_view_map(self):
        """the current measure to view map for the measurement map"""
        return self._measure_to_view_map

    def measure_int_put(self, measure, value):
        """associates the measure of type Int with the given value"""
        self._measurement_map[measure] = value

    def measure_float_put(self, measure, value):
        """associates the measure of type Float with the given value"""
        self._measurement_map[measure] = value

    def record(self, tag_map_tags):
        """records all the measures at the same time with an explicit tag_map
        """
        self.measure_to_view_map.MeasureToViewMap.record(
                tags=tag_map_tags,
                stats=self.measurement_map,
                timestamp=datetime.utcnow().isoformat() + 'Z'
        )
