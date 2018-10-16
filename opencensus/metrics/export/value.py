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


class Value(object):
    """The actual point value for a Point.
    Currently there are four types of Value:
     <ul>
       <li>double
       <li>long
       <li>Summary
       <li>Distribution (TODO(mayurkale): add Distribution class)
     </ul>
    Each Point contains exactly one of the four Value types.
    """

    def __init__(self, value):
        self._value = value

    @staticmethod
    def double_value(value):
        """Returns a double Value

        :type value: float
        :param value: value in double
        """
        return ValueDouble(value)

    @staticmethod
    def long_value(value):
        """Returns a long Value

        :type value: long
        :param value: value in long
        """
        return ValueLong(value)

    @staticmethod
    def summary_value(value):
        """Returns a summary Value

        :type value: Summary
        :param value: value in Summary
        """
        return ValueSummary(value)

    @property
    def value(self):
        """Returns the value."""
        return self._value


class ValueDouble(Value):
    """A 64-bit double-precision floating-point number.

    :type value: float
    :param value: the value in float.
    """

    def __init__(self, value):
        super(ValueDouble, self).__init__(value)


class ValueLong(Value):
    """A 64-bit integer.

    :type value: long
    :param value: the value in long.
    """

    def __init__(self, value):
        super(ValueLong, self).__init__(value)


class ValueSummary(Value):
    """Represents a snapshot values calculated over an arbitrary time window.

    :type value: summary
    :param value: the value in summary.
    """

    def __init__(self, value):
        super(ValueSummary, self).__init__(value)


class Exemplar(object):
    """An example point to annotate a given value in a bucket.

    Exemplars are example points that may be used to annotate aggregated
    Distribution values. They are metadata that gives information about a
    particular value added to a Distribution bucket.

    :type value: double
    :param value: Value of the exemplar point, determines which bucket the
    exemplar belongs to.

    :type timestamp: str
    :param timestamp: The observation (sampling) time of the exemplar value.

    :type attachments: dict(str, str)
    :param attachments: Contextual information about the example value.
    """

    def __init__(self, value, timestamp, attachments):
        self._value = value
        self._timestamp = timestamp
        self._attachments = attachments

    @property
    def value(self):
        return self._value

    @property
    def timestamp(self):
        return self._timestamp

    @property
    def attachments(self):
        return self._attachments


class Bucket(object):
    """A bucket of a histogram.

    :type count: int
    :param count: The number of values in each bucket of the histogram.

    :type exemplar: Exemplar
    :param exemplar: Optional exemplar for this bucket, omit if the
    distribution does not have a histogram.
    """

    def __init__(self, count, exemplar):
        self._count = count
        self._exemplar = exemplar

    @property
    def count(self):
        return self._count

    @property
    def exemplar(self):
        return self._exemplar


def window(ible, width):
    win = []
    for x in ible:
        win = (win + [x])[-width:]
        if len(win) == width:
            yield win


class ValueDistribution(Value):
    """Summary statistics for a population of values.

    Distribution contains summary statistics for a population of values. It
    optionally contains a histogram representing the distribution of those
    values across a set of buckets.

    :type count: int
    :param count: The number of values in the population.

    :type sum_: float
    :param sum_: The sum of the values in the population.

    :type sum_of_squared_deviation: float
    :param sum_of_squared_deviation: The sum of squared deviations from the
    mean of the values in the population.

    TODO: update to BucketOptions
    :type bucket_bounds: list(float)
    :param bucket_bounds: Bucket boundaries for the histogram of the values in
    the population.

    :type buckets: list(:class: 'Bucket')
    :param buckets: Histogram buckets for the given bucket boundaries.
    """

    def __init__(self, count, sum_, sum_of_squared_deviation, bucket_bounds,
                 buckets):
        if count < 0:
            raise ValueError("count must be non-negative")
        elif count == 0:
            if sum_ != 0:
                raise ValueError("sum_ must be 0 if count is 0")
            if sum_of_squared_deviation != 0:
                raise ValueError("sum_of_squared_deviation must be 0 if count "
                                 "is 0")
        if not bucket_bounds:
            if buckets is not None:
                raise ValueError("buckets must be null if bucket_bounds is "
                                 "empty")
        else:
            for (lo, hi) in window(bucket_bounds, 2):
                if lo >= hi:
                    raise ValueError("bucket_bounds must be monotonically "
                                     "increasing")
            if count != sum(bucket.count for bucket in buckets):
                raise ValueError("The distribution count must equal the sum "
                                 "of bucket counts")
        self._count = count
        self._sum = sum_
        self._sum_of_squared_deviation = sum_of_squared_deviation
        self._bucket_bounds = bucket_bounds
        self._buckets = buckets

    @property
    def count(self):
        return self._count

    @property
    def sum(self):
        return self._sum

    @property
    def sum_of_squared_deviation(self):
        return self._sum_of_squared_deviation

    @property
    def bucket_bounds(self):
        return self._bucket_bounds

    @property
    def buckets(self):
        return self._buckets
