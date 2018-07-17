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


class TagKey(object):
    """ A tag key with a property name

    :type name: str
    :param name: The name of the key

    """
    def __init__(self, name):
        self._name = name

    @property
    def name(self):
        """The name of the current key"""
        return self._name

    def is_valid_name(self, name):
        """Checks if the name of the key is valid

        :type name: str
        :param name: name to check

        :rtype: bool
        :returns: True if it valid, else returns False
        """
        if (len(name) > 0) and (len(name) <= 255):
            if (all(ord(char) < 126 for char in name) and
                    all(ord(char) > 32 for char in name)):
                return True
            else:
                return False
        else:
            return False
