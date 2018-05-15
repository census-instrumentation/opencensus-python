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


class TagValue(object):
    """ The value of a tag

    :type value: str
    :param value: A string representing the value of a key in a tag

    """
    def __init__(self, value):
        self._value = value

    @property
    def value(self):
        """The current value"""
        return self._value

    def is_valid_value(self, value):
        """ Checks if the value if valid

        :type value: str
        :param value: the value to be checked

        :rtype: bool
        :returns: True if valid, if not, False.

        """
        if len(value) <= 255:
            if (all(ord(char) < 126 for char in value) and
                    all(ord(char) > 32 for char in value)):
                return True
            else:
                return False
        else:
            return False
