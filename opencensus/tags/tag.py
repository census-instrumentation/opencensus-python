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

class Tag(object):

    def __init__(self, key, value):
        self._key = tag_key.TagKey(key)
        self._value = tag_value.TagValue(value)

    @property
    def key(self):
        return self._key

    @property
    def value(self):
        return self._value
