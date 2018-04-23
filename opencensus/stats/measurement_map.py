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
from opencensus.tags import tag_context
from opencensus.stats import measurement


class MeasurementMap(object):

    def __init__(self, meausrement_map=None):
        self._measurement_map = meausrement_map or {}

    def measure_int_put(self, key, value):
        tag_context.TagContext.put(tag_context.TagContext(measure.MeasureInt), key, value)

    def measure_float_put(self, key, value):
        tag_context.TagContext.put(tag_context.TagContext(measure.MeasureFloat), key, value)

    def record(self, tag_context_tags):
        if len(self._measurement_map) == 0:
            return

        record_bool = True
        for measurement.Measurement in self._measurement_map:
            if measurement != {}:
                record_bool = True

        if record_bool is False:
            return
