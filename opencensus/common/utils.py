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

from functools import wraps
import calendar
import datetime
import weakref

UTF8 = 'utf-8'

# Max length is 128 bytes for a truncatable string.
MAX_LENGTH = 128

ISO_DATETIME_REGEX = '%Y-%m-%dT%H:%M:%S.%fZ'


def _get_truncatable_str(str_to_convert):
    """Truncate a string if exceed limit and record the truncated bytes
    count.
    """
    truncated, truncated_byte_count = check_str_length(
        str_to_convert, MAX_LENGTH)

    result = {
        'value': truncated,
        'truncated_byte_count': truncated_byte_count,
    }
    return result


def check_str_length(str_to_check, limit=MAX_LENGTH):
    """Check the length of a string. If exceeds limit, then truncate it.

    :type str_to_check: str
    :param str_to_check: String to check.

    :type limit: int
    :param limit: The upper limit of the length.

    :rtype: tuple
    :returns: The string it self if not exceeded length, or truncated string
              if exceeded and the truncated byte count.
    """
    str_bytes = str_to_check.encode(UTF8)
    str_len = len(str_bytes)
    truncated_byte_count = 0

    if str_len > limit:
        truncated_byte_count = str_len - limit
        str_bytes = str_bytes[:limit]

    result = str(str_bytes.decode(UTF8, errors='ignore'))

    return (result, truncated_byte_count)


def timestamp_to_microseconds(timestamp):
    """Convert a timestamp string into a microseconds value
    :param timestamp
    :return time in microseconds
    """
    timestamp_str = datetime.datetime.strptime(timestamp, ISO_DATETIME_REGEX)
    epoch_time_secs = calendar.timegm(timestamp_str.timetuple())
    epoch_time_mus = epoch_time_secs * 1e6 + timestamp_str.microsecond
    return epoch_time_mus


def iuniq(ible):
    """Get an iterator over unique items of `ible`."""
    items = set()
    for item in ible:
        if item not in items:
            items.add(item)
            yield item


def uniq(ible):
    """Get a list of unique items of `ible`."""
    return list(iuniq(ible))


def window(ible, length):
    """Split `ible` into multiple lists of length `length`.

    >>> list(window(range(5), 2))
    [[0, 1], [2, 3], [4]]
    """
    if length <= 0:  # pragma: NO COVER
        raise ValueError
    ible = iter(ible)
    while True:
        elts = [xx for ii, xx in zip(range(length), ible)]
        if elts:
            yield elts
        else:
            break


class WeakrefWrapper(object):
    """Wrapper for weak references to bound methods.

    See the O'Reilley Python Cookbook for a pre-2.6 implementation:
    - https://www.oreilly.com/library/view/python-cookbook/0596001673/ch05s15.html
    - https://github.com/ActiveState/code/blob/master/recipes/Python/81253_WeakMethod/recipe-81253.py
    """  # noqa
    def __init__(self, obj, func):
        self.__self__ = weakref.ref(obj)
        self.__func__ = weakref.ref(func)

    def __call__(self):
        if self.__self__() is None:
            return None

        @wraps(self.__func__())
        def wrapped_func(*args, **kws):
            return self.__func__()(self.__self__(), *args, **kws)

        return wrapped_func


def get_weakref(func):
    """Get a weak reference to bound or unbound `func`.

    If `func` is unbound (i.e. has no __self__ attr) get a weakref.ref,
    otherwise get a wrapper that simulates simulates weakref.ref.
    """
    if func is None:
        raise ValueError
    try:
        return WeakrefWrapper(func.__self__, func.__func__)
    except AttributeError:
        return weakref.ref(func)
