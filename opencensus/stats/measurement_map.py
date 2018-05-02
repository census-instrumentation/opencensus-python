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

from opencensus.stats import measure
from opencensus.tags import tag_map
from opencensus.stats.measure_to_view_map import MeasureToViewMap
from opencensus.stats import measurement
from datetime import datetime


class MeasurementMap(object):

    def __init__(self, measure_to_view_map):
        self._measurement_map = {}
        self._measure_to_view_map = measure_to_view_map

    @property
    def measurement_map(self):
        return self._measurement_map

    @property
    def measure_to_view_map(self):
        return self._measure_to_view_map

    def measure_int_put(self, key, value):
        self._measurement_map[key] = value

    def measure_float_put(self, key, value):
        self._measurement_map[key] = value

    def record(self, tag_map_tags):
        self.measure_to_view_map.MeasureToViewMap.record(self._measure_to_view_map, tags=tag_map_tags, stats=self.measurement_map, timestamp=datetime.utcnow().isoformat() + 'Z')
