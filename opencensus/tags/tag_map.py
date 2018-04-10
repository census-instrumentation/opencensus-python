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

    def __init__(self, tags=None, map=None):
        if map is None:
            self.map = {}
        else:
            self.map = map
        if tags is not None:
            self.tags = tags
            print(self.tags)
            for tag in self.tags:
                print(tag)
                for tag_key, tag_value in tag.items():
                    self.map[tag_key] = tag_value

        else:
            self.tags = {}

    def insert(self, key, value):
        if key in self.map:
            return
        else:
            self.map[key] = value

    def delete(self, key):
        self.map.pop(key, None)

    def update(self, key, value):
        if key in self.map:
            self.map[key] = value

    def tag_key_exists(self, key):
        if key in self.map:
            return True
        else:
            return False

    def get_value(self, key):
        if key in self.map:
            return self.map[key]
        else:
            return "key is not in map"
