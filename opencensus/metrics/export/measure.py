# Copyright 2019, OpenCensus Authors
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

from opencensus.metrics.export import measurement

class Measure(object):
    """ A measure is the type of metric used in capturing raw measurements
    that is being recorded with a name, measure_type, description, and unit

    :type name: str
    :param name: string representing the name of the measure

    :type measure_type: measure.MeasureType
    :param measure_type: an int representing the measure_type of the measure

    :type description: str
    :param description: a string representing the description of the measure

    :type unit: str
    :param unit: the units in which the measure values are measured

    :type measure_type: measure.AggregationType
    :param measure_type: an int representing the aggregation_type of the measure

    """
    def __init__(self, name, measure_type, description, unit, aggregation_type):
        self._name = name
        self._measure_type = measure_type
        self._description = description
        self._unit = unit
        self._aggregation_type = aggregation_type

    @property
    def name(self):
        """The name of the current measure"""
        return self._name

    @property
    def measure_type(self):
        """The type of the current measure"""
        return self._measure_type

    @property
    def description(self):
        """The description of the current measure"""
        return self._description

    @property
    def unit(self):
        """The unit of the current measure"""
        return self._unit

    @property
    def aggregation_type(self):
        """The aggregation type of the current measure"""
        return self._aggregation_type

    def create_double_measurement(self, value):
        if self._measure_type != MeasureType.DOUBLE:
            raise ValueError("Measure is of wrong type")
        if not isinstance(value, float):
            raise ValueError("Value: " + value + " is not a double") 
        return measurement.MeasurementDouble(value)

    def create_long_measurement(self, value):
        if self._measure_type != MeasureType.LONG:
            raise ValueError("Measure is of wrong type")
        if not isinstance(value, int):
            raise ValueError("Value: " + value + " is not a long") 
        return measurement.MeasurementLong(value)

class MeasureType(object):
    LONG = 0
    DOUBLE = 1

class AggregationType(object):
    COUNT = 0
    SUM = 1
