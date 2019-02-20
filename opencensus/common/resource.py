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
import re


# Matches anything outside ASCII 32-126 inclusive
NON_PRINTABLE_ASCII = re.compile(
    r'[^ !"#$%&\'()*+,\-./:;<=>?@\[\\\]^_`{|}~0-9a-zA-Z]')


def merge_resources(r1, r2):
    """Merge two resources to get a new resource.

    :type r1: :class:`Resource`
    :param r1: The first resource to merge, takes priority in conflicts.

    :type r2: :class:`Resource`
    :param r2: The second resource to merge.

    :rtype: :class:`Resource`
    :return: The new combined resource.
    """
    type_ = r1.type or r2.type
    labels = copy(r2.labels)
    labels.update(r1.labels)
    return Resource(type_, labels)


def check_ascii_256(string):
    """Check that `string` is printable ASCII and at most 256 chars.

    Raise a `ValueError` if this check fails. Note that `string` itself doesn't
    have to be ASCII-encoded.

    :type string: str
    :param string: The string to check.
    """
    if string is None:
        return
    if len(string) > 256:
        raise ValueError("Value is longer than 256 characters")
    bad_char = NON_PRINTABLE_ASCII.search(string)
    if bad_char:
        raise ValueError(u'Character "{}" at position {} is not printable '
                         'ASCII'
                         .format(
                             string[bad_char.start():bad_char.end()],
                             bad_char.start()))


class Resource(object):
    """A description of the entity for which signals are reported.

    `type_` and `labels`' keys and values should contain only printable ASCII
    and should be at most 256 characters.

    See:
        https://github.com/census-instrumentation/opencensus-specs/blob/master/resource/Resource.md

    :type type_: str
    :param type_: The resource type identifier.

    :type labels: dict
    :param labels: Key-value pairs that describe the entity.
    """  # noqa

    def __init__(self, type_=None, labels=None):
        if type_ is not None and not type_:
            raise ValueError("Resource type must not be empty")
        check_ascii_256(type_)
        if labels is None:
            labels = {}
        for key, value in labels.items():
            if not key:
                raise ValueError("Resource key must not be null or empty")
            if value is None:
                raise ValueError("Resource value must not be null")
            check_ascii_256(key)
            check_ascii_256(value)

        self.type = type_
        self.labels = copy(labels)

    def get_type(self):
        """Get this resource's type.

        :rtype: str
        :return: The resource's type.
        """
        return self.type

    def get_labels(self):
        """Get this resource's labels.

        :rtype: dict
        :return: The resource's label dict.
        """
        return copy(self.labels)

    def merge(self, other):
        """Get a copy of this resource combined with another resource.

        The combined resource will have the union of both resources' labels,
        keeping this resource's label values if they conflict.

        :type other: :class:`Resource`
        :param other: The other resource to merge.

        :rtype: :class:`Resource`
        :return: The new combined resource.
        """
        return merge_resources(self, other)
