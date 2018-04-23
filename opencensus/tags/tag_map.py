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

from opencensus.tags import tag
from opencensus.tags import tag_key
from opencensus.tags import tag_value


class TagMap(object):
    """ A tag map is a map of tags from key to value

    :type tags: list(:class: '~opencensus.tags.tag.Tag')
    :param tags: a list of tags

    :type map: dict
    :param map: a map of the tags

    """
    def __init__(self, tags=None, map=None):
        self.map = map or {}
        if tags is not None:
            self.tags = tags
            for tag in self.tags:
                for tag_key, tag_value in tag.items():
                    self.map[tag_key] = tag_value

        else:
            self.tags = {}

    def insert(self, key, value):
        """Inserts a key and value in the map if the map does not already contain the key.

        :type key: :class: '~opencensus.tags.tag_key.TagKey'
        :param key: a tag key to insert into the map

        :type value: :class: '~opencensus.tags.tag_value.TagValue'
        :param value: a tag value to insert into the tag map and associated with the tag key

        """
        if key in self.map:
            return
        else:
            self.map[key] = value

    def delete(self, key):
        """ Deletes a tag from the map if the key is in the map

        :type key: str
        :param key: A string representing a possible tag key

        :returns: the value of the key in the dictionary if it is in there, or None if it is not.
        """
        self.map.pop(key, None)

    def update(self, key, value):
        """ Updates the map by updating the value of a key

        :type key: :class: '~opencensus.tags.tag_key.TagKey'
        :param key: A tag key to be updated

        :type value: str
        :param value: The value to update the key to in the map

        """
        if key in self.map:
            self.map[key] = value

    def tag_key_exists(self, key):
        """ Checking if the tag key exists in the map

        :type key: str
        :param key: A string to check to see if that is a key in the map

        :returns: True if the key is in map, False is it is not

        """
        return key in self.map

    def get_value(self, key):
        """ Gets the value of the key passed in if the key exists in the map

        :type key: str
        :param key: A string representing a key to get the value of in the map

        :returns: A KeyError if the value is None, else returns the value
        """
        value = self.map.get(key, None)
        if value is None:
            raise KeyError('Key is not in map.')

        return value
