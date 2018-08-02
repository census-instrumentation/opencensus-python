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
from opencensus.tags.validation import is_legal_chars

_TAG_VALUE_ERROR = 'tag value must not be longer than 255 characters and of ascii values between 32 - 126'


class TagValue(object):
    """ The value of a tag

    :type value: str
    :param value: A string representing the value of a key in a tag

    """

    def __init__(self, value):
        if not TagValue.is_valid_value(value):
            raise ValueError(_TAG_VALUE_ERROR)
        self._value = value

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, val):
        if not TagValue.is_valid_value(val):
            raise ValueError(_TAG_VALUE_ERROR)
        self._value = val

    @staticmethod
    def is_valid_value(value):
        """ Checks if the value if valid

        :type value: str
        :param value: the value to be checked

        :rtype: bool
        :returns: True if valid, if not, False.

        """
        return is_legal_chars(value) if len(value) <= 255 else False
