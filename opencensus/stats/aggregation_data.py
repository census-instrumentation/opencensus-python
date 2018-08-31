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
from opencensus.stats import bucket_boundaries


class BaseAggregationData(object):
    """Aggregation Data represents an aggregated value from a collection

    :type aggregation_data: aggregated value
    :param aggregation_data: represents the aggregated value from a collection

    """
    def __init__(self, aggregation_data):
        self._aggregation_data = aggregation_data

    @property
    def aggregation_data(self):
        """The current aggregation data"""
        return self._aggregation_data


class SumAggregationDataFloat(BaseAggregationData):
    """Sum Aggregation Data is the aggregated data for the Sum aggregation

    :type sum_data: float
    :param sum_data: represents the aggregated sum

    """
    def __init__(self, sum_data):
        super(SumAggregationDataFloat, self).__init__(sum_data)
        self._sum_data = sum_data

    def add_sample(self, value, timestamp=None, attachments=None):
        """Allows the user to add a sample to the Sum Aggregation Data
        The value of the sample is then added to the current sum data
        """
        self._sum_data += value

    @property
    def sum_data(self):
        """The current sum data"""
        return self._sum_data


class CountAggregationData(BaseAggregationData):
    """Count Aggregation Data is the count value of aggregated data

    :type count_data: long
    :param count_data: represents the aggregated count

    """
    def __init__(self, count_data):
        super(CountAggregationData, self).__init__(count_data)
        self._count_data = count_data

    def add_sample(self, value, timestamp=None, attachments=None):
        """Adds a sample to the current Count Aggregation Data and adds 1 to
        the count data"""
        self._count_data = self._count_data + 1

    @property
    def count_data(self):
        """The current count data"""
        return self._count_data


class DistributionAggregationData(BaseAggregationData):
    """Distribution Aggregation Data refers to the distribution stats of
    aggregated data

    :type mean_data: float
    :param mean_data: the mean value of the distribution

    :type count_data: int
    :param count_data: the count value of the distribution

    :type min_: double
    :param min_: the minimum value of the distribution

    :type max_: double
    :param max_: the maximum value of the distribution

    :type sum_of_sqd_deviations: float
    :param sum_of_sqd_deviations: the sum of the sqd deviations from the mean

    :type counts_per_bucket: list(int)
    :param counts_per_bucket: the number of occurrences per bucket

    :type exemplars: list(Exemplar)
    :param: exemplars: the exemplars associated with histogram buckets.

    :type bounds: list(float)
    :param bounds: the histogram distribution of the values

    """
    def __init__(self,
                 mean_data,
                 count_data,
                 min_,
                 max_,
                 sum_of_sqd_deviations,
                 counts_per_bucket=None,
                 bounds=None,
                 exemplars=None):
        super(DistributionAggregationData, self).__init__(mean_data)
        self._mean_data = mean_data
        self._count_data = count_data
        self._min = min_
        self._max = max_
        self._sum_of_sqd_deviations = sum_of_sqd_deviations
        if bounds is None:
            bounds = []

        if counts_per_bucket is None:
            counts_per_bucket = []
            bucket_size = len(bounds) + 1
            for i in range(bucket_size):
                counts_per_bucket.append(0)
        self._counts_per_bucket = counts_per_bucket
        self._bounds = bucket_boundaries.BucketBoundaries(
                                            boundaries=bounds).boundaries
        bucket = 0
        for _ in self.bounds:
            bucket = bucket + 1

        # If there is no histogram, do not record an exemplar
        self._exemplars = \
            {bucket: exemplars} if len(self._bounds) > 0 else None

    @property
    def mean_data(self):
        """The current mean data"""
        return self._mean_data

    @property
    def count_data(self):
        """The current count data"""
        return self._count_data

    @property
    def min(self):
        """The current min value"""
        return self._min

    @property
    def max(self):
        """The current max value"""
        return self._max

    @property
    def sum_of_sqd_deviations(self):
        """The current sum of squared deviations from the mean"""
        return self._sum_of_sqd_deviations

    @property
    def counts_per_bucket(self):
        """The current counts per bucket for the distribution"""
        return self._counts_per_bucket

    @property
    def exemplars(self):
        """The current counts per bucket for the distribution"""
        return self._exemplars

    @property
    def bounds(self):
        """The current bounds for the distribution"""
        return self._bounds

    @property
    def sum(self):
        """The sum of the current distribution"""
        return self._mean_data * self._count_data

    @property
    def variance(self):
        """The variance of the current distribution"""
        if self._count_data <= 1:
            return 0
        return self.sum_of_sqd_deviations / (self._count_data - 1)

    def add_sample(self, value, timestamp, attachments):
        """Adding a sample to Distribution Aggregation Data"""
        if value < self.min:
            self._min = value
        if value > self.max:
            self._max = value
        self._count_data += 1
        bucket = self.increment_bucket_count(value)

        if attachments is not None and self.exemplars is not None:
            self.exemplars[bucket] = Exemplar(value, timestamp, attachments)
        if self.count_data == 1:
            self._mean_data = value
            return

        old_mean = self._mean_data
        self._mean_data = self._mean_data + (
                          (value - self._mean_data) / self._count_data)
        self._sum_of_sqd_deviations = self._sum_of_sqd_deviations + (
                                      (value - old_mean) *
                                      (value - self._mean_data))

    def increment_bucket_count(self, value):
        """Increment the bucket count based on a given value from the user"""
        i = 0
        incremented = False
        for b in self._bounds:
            if value < b and not incremented:
                self._counts_per_bucket[i] += 1
                incremented = True
            i += 1

        if incremented:
            return i

        if len(self._bounds) == 0:
            self._counts_per_bucket[0] += 1
            return i

        self._counts_per_bucket[(len(self._bounds))-1] += 1
        return i


class LastValueAggregationData(BaseAggregationData):
    """
    LastValue Aggregation Data is the value of aggregated data

    :type value: long
    :param value: represents the current value

    """
    def __init__(self, value):
        super(LastValueAggregationData, self).__init__(value)
        self._value = value

    def add_sample(self, value, timestamp=None, attachments=None):
        """Adds a sample to the current
        LastValue Aggregation Data and overwrite
        the current recorded value"""
        self._value = value

    @property
    def value(self):
        """The current value recorded"""
        return self._value


class Exemplar(object):
    """ Exemplar represents an example point that may be used to annotate
        aggregated distribution values, associated with a histogram bucket.

        :type value: double
        :param value: value of the Exemplar point.

        :type timestamp: time
        :param timestamp: the time that this Exemplar's value was recorded.

        :type attachments: dict
        :param attachments: the contextual information about the example value.
    """

    def __init__(self,
                 value,
                 timestamp,
                 attachments):
        self._value = value

        self._timestamp = timestamp

        if attachments is None:
            raise TypeError('attachments should not be empty')

        for key, value in attachments.items():
            if key is None or not isinstance(key, str):
                raise TypeError('attachment key should not be '
                                'empty and should be a string')
            if value is None or not isinstance(value, str):
                raise TypeError('attachment value should not be '
                                'empty and should be a string')
        self._attachments = attachments

    @property
    def value(self):
        """The current value of the Exemplar point"""
        return self._value

    @property
    def timestamp(self):
        """The time that this Exemplar's value was recorded"""
        return self._timestamp

    @property
    def attachments(self):
        """The contextual information about the example value"""
        return self._attachments
