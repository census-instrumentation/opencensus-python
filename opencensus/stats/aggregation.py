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

    def __init__(self, aggregation_type=None, buckets=None):
        if aggregation_type is not None:
            self._aggregation_type = aggregation_type
        else:
            self._aggregation_type = "none"

        if buckets is not None:
            self._buckets = buckets
        else:
            self._buckets = []

    @property
    def aggregation_type(self):
        return self._aggregation_type

    @property
    def buckets(self):
        return self._buckets


class SumAggregation(BaseAggregation):
    def __init__(self, sum=None, aggregation_type="sum"):
        super().__init__(aggregation_type)
        self._aggregation_type = aggregation_type
        if sum is not None:
            self._sum = aggregation_data.SumAggregationDataFloat(sum_data=sum)
        else:
            self._sum = aggregation_data.SumAggregationDataFloat(sum_data=0)

    @property
    def aggregation_type(self):
        return self._aggregation_type

    @property
    def sum(self):
        return self._sum

class CountAggregation(BaseAggregation):
    def __init__(self, count=None, aggregation_type="count"):
        super().__init__(aggregation_type)
        self._aggregation_type = aggregation_type
        if count is not None:
            self._count = aggregation_data.CountAggregationData(count)
        else:
            self._count = aggregation_data.CountAggregationData(0)

    @property
    def aggregation_type(self):
        return self._aggregation_type

    @property
    def count(self):
        return self._count

class MeanAggregation(BaseAggregation):
    def __init__(self, mean=None, count=None, aggregation_type="mean"):
        super().__init__(aggregation_type)
        self._aggregation_type = aggregation_type
        if count is not None:
            self._count = count
        else:
            self._count = 0
        if mean is not None:
            self._mean = aggregation_data.MeanAggregationData(mean, self._count)
        else:
            self._mean = aggregation_data.MeanAggregationData(0, self._count)

    @property
    def aggregation_type(self):
        return self._aggregation_type

    @property
    def count(self):
        return self._count

    @property
    def mean(self):
        return self._mean

class DistributionAggregation(BaseAggregation):
    def __init__(self, boundaries=None, distribution=None, aggregation_type="distribution"):
        super().__init__(aggregation_type, boundaries)
        self._aggregation_type = aggregation_type
        self._boundaries = bucket_boundaries.BucketBoundaries(boundaries)
        self._distribution = dict(distribution or {})

    @property
    def aggregation_type(self):
        return self._aggregation_type

    @property
    def boundaries(self):
        return self._boundaries

    @property
    def distribution(self):
        return self._distribution
