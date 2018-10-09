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


class Point(object):
    """A timestamped measurement of a TimeSeries.

    :type value: Value
    :param value: the Value of the Point.

    :type timestamp: time
    :param timestamp: the Timestamp when the Point was recorded.
    """

    def __init__(self, value, timestamp):
        self._value = value
        self._timestamp = timestamp

    @property
    def value(self):
        """Returns the Value"""
        return self._value

    @property
    def timestamp(self):
        """Returns the Timestamp when this Point was recorded."""
        return self._timestamp
