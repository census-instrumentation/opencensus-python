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

from opencensus.tags import tag_key
from opencensus.tags import tag_value

class TagContext(object):

    def __init__(self, tags=None):
        self._tags = dict(tags or {})

    def put(self, key, value):
        self._tags[key] = value

    def remove(self, key):
        self._tags.pop(key, None)

    @property
    def tags(self):
        return self._tags

    def get_tag_value(self, key):
        if key in self._tags:
            return self._tags[key]
