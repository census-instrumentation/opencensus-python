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

_TAG_NAME_ERROR = 'tag name must not be empty, no longer than 255 characters and of ascii values between 32 - 126'


class TagKey(object):
    """ A tag key with a property name

    :type name: str
    :param name: The name of the key

    """

    def __init__(self, name):
        if not TagKey.is_valid_name(name):
            raise ValueError(_TAG_NAME_ERROR)
        self._name = name

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.name == other.name

    def __hash__(self):
        return hash(self.name)

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, val):
        if not TagKey.is_valid_name(val):
            raise ValueError(_TAG_NAME_ERROR)
        self._name = val

    @staticmethod
    def is_valid_name(name):
        """Checks if the name of the key is valid

        :type name: str
        :param name: name to check

        :rtype: bool
        :returns: True if it valid, else returns False
        """

        return is_legal_chars(name) if 0 < len(name) <= 255 else False
