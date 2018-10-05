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


class Value(object):
    """The actual point value for a Point.
    Currently there are four types of Value:
     <ul>
       <li>double
       <li>long
       <li>Summary
       <li>Distribution (TODO(mayurkale): add Distribution class)
     </ul>
    Each Point contains exactly one of the four Value types.
    """
    def __init__(self, value):
        self._value = value

    @staticmethod
    def double_value(value):
        """Returns a double Value

        :type value: float
        :param value: value in double
        """
        return ValueDouble(value)

    @staticmethod
    def long_value(value):
        """Returns a long Value

        :type value: long
        :param value: value in long
        """
        return ValueLong(value)

    @staticmethod
    def summary_value(value):
        """Returns a summary Value

        :type value: Summary
        :param value: value in Summary
        """
        return ValueSummary(value)

    @property
    def get_value(self):
        """Returns the value."""
        return self._value


class ValueDouble(Value):
    """A 64-bit double-precision floating-point number.

    :type value: float
    :param value: the value in float.
    """
    def __init__(self, value):
        super(ValueDouble, self).__init__(value)


class ValueLong(Value):
    """A 64-bit integer.

    :type value: long
    :param value: the value in long.
    """
    def __init__(self, value):
        super(ValueLong, self).__init__(value)


class ValueSummary(Value):
    """Represents a snapshot values calculated over an arbitrary time window.

    :type value: summary
    :param value: the value in summary.
    """
    def __init__(self, value):
        super(ValueSummary, self).__init__(value)
