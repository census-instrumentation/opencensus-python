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

import time

from opencensus.ext.azure.common import utils

class Measurement(object):
    """ A measurement is an object with a value and timestamp attached to it
        It represents a single raw data point
        The timestamp is set to the current time that the Measurement is created

    :type value: long or double
    :param value: value of the measurement


    """
    def __init__(self, value):
        self._value = value
        self._timestamp = utils.to_iso_str()

    @property
    def value(self):
        """The value of the current measurement"""
        return self._value
    
    @property
    def timestamp(self):
        """The value of the current measurement"""
        return self._timestamp


class MeasurementLong(Measurement):
    """ Creates a new Long Measurement """
    def __init__(self, value):
        super(MeasurementLong, self).__init__(value)


class MeasurementDouble(Measurement):
    """ Creates a new Double Measurement """
    def __init__(self, value):
        super(MeasurementDouble, self).__init__(value)
