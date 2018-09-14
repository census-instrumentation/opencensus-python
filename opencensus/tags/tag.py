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

from collections import namedtuple

Tag_ = namedtuple('Tag', ['key', 'value'])


class Tag(Tag_):
    """A tag, in the format [KEY]:[VALUE].

    :type key: '~opencensus.tags.tag_key.TagKey'
    :param key: Key in the tag

    :type value: '~opencensus.tags.tag_key.TagValue'
    :param value: Value of the key in the tag.

    """
    pass
