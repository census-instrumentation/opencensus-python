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

    :type measure_type: MeasureType
    :param measure_type: a string representing the measure_type of the measure

    :type description: str
    :param description: a string representing the description of the measure

    :type unit: str
    :param unit: the units in which the measure values are measured

    """
    def __init__(self, name, measure_type, description="", unit="1"):
        self._name = name
        self._measure_type = measure_type
        self._description = description
        self._unit = unit
        self._measurement = None

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
    def measurement(self):
        """The current measurement of the measure"""
        return self._measurement

    def create_measurement(self, value):
        if self._measure_type == MeasureType.LONG:
            if not isinstance(value, int):
                raise ValueError("Value: " + value + " is not a long") 
            self._measurement = measurement.MeasurementLong(value)
        else:
            if not isinstance(value, float):
                raise ValueError("Value: " + value + " is not a double") 
            self._measurement = measurement.MeasurementDouble(value)

    def has_measurement(self):
        return self._measurement is not None

class Builder(object):
    """ A measure Builder is used to construct instances of Measure """

    def __init__(self, name, measure_type, description="", unit="1"):
        self._name = name
        self._measure_type = measure_type
        self._description = description
        self._unit = unit

    @property
    def name(self):
        """The current name of the builder"""
        return self._name

    @property
    def measure_type(self):
        """The current type of the builder"""
        return self.measure_type

    @property
    def description(self):
        """The current description of the builder"""
        return self._description

    @property
    def unit(self):
        """The current unit of the builder"""
        return self._unit

    def build(self):
        return Measure(self._name, self._measure_type, self._description, self._unit)

class MeasureType(object):
    LONG = 1
    DOUBLE = 2
