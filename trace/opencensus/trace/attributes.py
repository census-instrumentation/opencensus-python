# Copyright 2017, OpenCensus Authors
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


def _format_attribute_value(value):
    if isinstance(value, str):
        value_type = 'string_value'
    elif isinstance(value, int):
        value_type = 'int_value'
    elif isinstance(value, bool):
        value_type = 'bool_value'
    else:
        raise TypeError("Value must be str, int, or bool.")

    return {value_type: value}


class Attributes(object):
    """A set of attributes, each in the format [KEY]:[VALUE].
    
    :type attributes: dict
    :param attributes: The set of attributes. Each attribute's key can be up
                       to 128 bytes long. The value can be a string up to 256
                       bytes, an integer, or the Boolean values true and false.
    """
    def __init__(self, attributes=None):
        if attributes is None:
            attributes = {}

        self.attributes = attributes

    def set_attribute(self, key, value):
        """Set a key value pair."""
        self.attributes[key] = value

    def get_attribute(self, key):
        """Get a attribute value."""
        return self.attributes.get(key, None)

    def format_attributes_json(self):
        """Convert the Attributes object to json format."""
        attributes_json = {}

        for key in self.attributes:
            value = self.attributes.get(key)
            value_json = _format_attribute_value(value)
            attributes_json[key] = value_json

        return attributes_json
