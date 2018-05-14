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
from opencensus.stats import aggregation_data


class BaseAggregation(object):
    """Aggregation describes how the data collected is aggregated by type of
    aggregation and buckets

    :type buckets: list(:class: '~opencensus.stats.bucket_boundaries.
                                BucketBoundaries')
    :param buckets: list of endpoints if the aggregation represents a
                    distribution

    """
    def __init__(self, buckets=None):
        self._aggregation_type = "none"
        self._buckets = buckets or []

    @property
    def aggregation_type(self):
        """The aggregation type of the current aggregation"""
        return self._aggregation_type

    @property
    def buckets(self):
        """The buckets of the current aggregation"""
        return self._buckets


class SumAggregation(BaseAggregation):
    """Sum Aggregation escribes that data collected and aggregated with this
    method will be summed

    :type sum: int or float
    :param sum: the sum of the data collected and aggregated

    """
    def __init__(self, sum=None):
        super(SumAggregation, self).__init__()
        self._aggregation_type = "sum"
        if sum is not None:
            self._sum = aggregation_data.SumAggregationDataFloat(sum_data=sum)
        else:
            self._sum = aggregation_data.SumAggregationDataFloat(sum_data=0)

    @property
    def aggregation_type(self):
        """The aggregation type of the current aggregation"""
        return self._aggregation_type

    @property
    def sum(self):
        """The sum of the current aggregation"""
        return self._sum


class CountAggregation(BaseAggregation):
    """Describes that the data collected and aggregated with this method will
    be turned into a count value

    :type count: int
    :param count: represents the count of this aggregation

    """
    def __init__(self, count=0):
        super(CountAggregation, self).__init__()
        self._aggregation_type = "count"
        self._count = aggregation_data.CountAggregationData(count)

    @property
    def aggregation_type(self):
        """The aggregation type of the current aggregation"""
        return self._aggregation_type

    @property
    def count(self):
        """The count of the current aggregation"""
        return self._count


class DistributionAggregation(BaseAggregation):
    """Distribution Aggregation indicates that the desired aggregation is a
    histogram distribution

    :type boundaries: list(:class:'~opencensus.stats.bucket_boundaries.
                            BucketBoundaries')
    :param boundaries: the bucket endpoints

    :type distribution: histogram
    :param distribution: histogram of the values of the population

    """
    def __init__(self, boundaries=None, distribution=None):
        super(DistributionAggregation, self).__init__(boundaries)
        self._aggregation_type = "distribution"
        self._boundaries = bucket_boundaries.BucketBoundaries(boundaries)
        self._distribution = distribution if distribution is not None else {}

    @property
    def aggregation_type(self):
        """The aggregation type of the current aggregation"""
        return self._aggregation_type

    @property
    def boundaries(self):
        """The boundaries of the current aggregation"""
        return self._boundaries

    @property
    def distribution(self):
        """The distribution of the current aggregation"""
        return self._distribution
