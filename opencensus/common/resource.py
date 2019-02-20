# Copyright 2019 Google Inc.
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


from copy import copy


def merge_resources(r1, r2):
    type_ = r1.type or r2.type
    labels = copy(r2.labels)
    labels.update(r1.labels)
    return Resource(type_, labels)


class Resource(object):
    """A description of the entity for which signals are reported.

    See:
        https://github.com/census-instrumentation/opencensus-specs/blob/master/resource/Resource.md
    """  # noqa

    def __init__(self, type_=None, labels=None):
        if type_ is not None and not type_:
            raise ValueError("Resource type must not be empty")
        if labels is None:
            labels = {}
        for key, value in labels.items():
            if not key:
                raise ValueError("Resource key must not be null or empty")
            if value is None:
                raise ValueError("Resource value must not be null")

        self.type = type_
        self.labels = copy(labels)

    def get_type(self):
        return self.type

    def get_labels(self):
        return copy(self.labels)

    def merge(self, other):
        return merge_resources(self, other)
