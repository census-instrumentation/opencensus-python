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

    def add_sample(self, value):
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

    def add_sample(self, value):
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

    :type bounds: list(float)
    :param bounds: the histogram distribution of the values

    """
    def __init__(self,
                 mean_data,
                 count_data,
                 min_,
                 max_,
                 sum_of_sqd_deviations,
                 counts_per_bucket,
                 bounds):
        super(DistributionAggregationData, self).__init__(mean_data)
        self._mean_data = mean_data
        self._count_data = count_data
        self._min = min_
        self._max = max_
        self._sum_of_sqd_deviations = sum_of_sqd_deviations
        self._counts_per_bucket = counts_per_bucket
        self._bounds = bucket_boundaries.BucketBoundaries(
                                            boundaries=bounds).boundaries

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

    def add_sample(self, value):
        """Adding a sample to Distribution Aggregation Data"""
        if value < self.min:
            self._min = value
        if value > self.max:
            self._max = value
        self._count_data += 1
        self.increment_bucket_count(value)

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
        if len(self._bounds) == 0:
            self._counts_per_bucket[0] += 1
            return

        i = 0
        for b in self._bounds:
            if value < b:
                self._counts_per_bucket[i] += 1
                return
            i += 1

        self._counts_per_bucket[(len(self._bounds))-1] += 1
