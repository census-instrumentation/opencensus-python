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

class Measurement(object):
    def __init__(self, measure, value):
        self._measure = measure
        self._value = value

    @property
    def value(self):
        return self._value

    @property
    def measure(self):
        return self._measure

class MeasurementInt(Measurement):
    def __init__(self, measure, value):
        super().__init__(measure, value)

class MeasurementFloat(Measurement):
    def __init__(self, measure, value):
        super().__init__(measure, value)
