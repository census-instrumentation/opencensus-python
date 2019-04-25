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

import logging

from opencensus.stats import aggregation_data
from opencensus.stats import metric_utils
from opencensus.metrics.export.metric_descriptor import MetricDescriptorType


logger = logging.getLogger(__name__)


class Type(object):
    """ The type of aggregation function used on a View.

    Attributes:
      NONE (int): The aggregation type of the view is 'unknown'.
      SUM (int): The aggregation type of the view is 'sum'.
      COUNT (int): The aggregation type of the view is 'count'.
      DISTRIBUTION (int): The aggregation type of the view is 'distribution'.
      LASTVALUE (int): The aggregation type of the view is 'lastvalue'.
    """
    NONE = 0
    SUM = 1
    COUNT = 2
    DISTRIBUTION = 3
    LASTVALUE = 4


class BaseAggregation(object):
    """Aggregation describes how the data collected is aggregated by type of
    aggregation and buckets

    :type buckets: list(:class: '~opencensus.stats.bucket_boundaries.
                                BucketBoundaries')
    :param buckets: list of endpoints if the aggregation represents a
                    distribution

    :type aggregation_type: :class:`~opencensus.stats.aggregation.Type`
    :param aggregation_type: represents the type of this aggregation

    """
    def __init__(self, buckets=None, aggregation_type=Type.NONE):
        self._aggregation_type = aggregation_type
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


    :type aggregation_type: :class:`~opencensus.stats.aggregation.Type`
    :param aggregation_type: represents the type of this aggregation

    """
    def __init__(self, sum=None, aggregation_type=Type.SUM):
        super(SumAggregation, self).__init__(aggregation_type=aggregation_type)
        self._initial_sum = sum or 0

    def new_aggregation_data(self, measure):
        value_type = MetricDescriptorType.to_type_class(
            metric_utils.get_metric_type(measure, self.aggregation_type))
        # TODO: do we need to type cast `_initial_sum`?
        return aggregation_data.SumAggregationData(
            value_type=value_type, sum_data=self._initial_sum)


class CountAggregation(BaseAggregation):
    """Describes that the data collected and aggregated with this method will
    be turned into a count value

    :type count: int
    :param count: represents the count of this aggregation

    :type aggregation_type: :class:`~opencensus.stats.aggregation.Type`
    :param aggregation_type: represents the type of this aggregation

    """
    def __init__(self, count=0, aggregation_type=Type.COUNT):
        super(CountAggregation, self).__init__(
            aggregation_type=aggregation_type)
        self._initial_count = count

    def new_aggregation_data(self, _measure):
        return aggregation_data.CountAggregationData(self._initial_count)


class DistributionAggregation(BaseAggregation):
    """Distribution Aggregation indicates that the desired aggregation is a
    histogram distribution

    :type boundaries: list(:class:'~opencensus.stats.bucket_boundaries.
                            BucketBoundaries')
    :param boundaries: the bucket endpoints

    :type distribution: histogram
    :param distribution: histogram of the values of the population

    :type aggregation_type: :class:`~opencensus.stats.aggregation.Type`
    :param aggregation_type: represents the type of this aggregation

    """

    def __init__(self,
                 boundaries=None,
                 distribution=None,
                 aggregation_type=Type.DISTRIBUTION):
        if boundaries:
            if not all(boundaries[ii] < boundaries[ii + 1]
                       for ii in range(len(boundaries) - 1)):
                raise ValueError("bounds must be sorted in increasing order")
            for ii, bb in enumerate(boundaries):
                if bb > 0:
                    break
            else:
                ii += 1
            if ii:
                logger.warning("Dropping %s non-positive bucket boundaries",
                               ii)
            boundaries = boundaries[ii:]

        super(DistributionAggregation, self).__init__(
            buckets=boundaries, aggregation_type=aggregation_type)
        self._boundaries = boundaries

    def new_aggregation_data(self, _measure):
        return aggregation_data.DistributionAggregationData(
            0, 0, 0, None, self._boundaries)


class LastValueAggregation(BaseAggregation):
    """Describes that the data collected with this method will
    overwrite the last recorded value

    :type value: long
    :param value: represents the value of this aggregation

    :type aggregation_type: :class:`~opencensus.stats.aggregation.Type`
    :param aggregation_type: represents the type of this aggregation

    """
    def __init__(self, value=0, aggregation_type=Type.LASTVALUE):
        super(LastValueAggregation, self).__init__(
            aggregation_type=aggregation_type)
        self._initial_value = value

    def new_aggregation_data(self, measure):
        value_type = MetricDescriptorType.to_type_class(
            metric_utils.get_metric_type(measure, self.aggregation_type))
        return aggregation_data.LastValueAggregationData(
            value=self._initial_value, value_type=value_type)
