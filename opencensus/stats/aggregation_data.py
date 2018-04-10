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
    def __init__(self, aggregation_data):
        self.aggregation_data = aggregation_data

class SumAggregationDataFloat(BaseAggregationData):
    def __init__(self, sum_data):
        super().__init__(sum_data)
        self._sum_data = sum_data

    def add_sample(self, value):
        self._sum_data = self._sum_data + value

    @property
    def sum_data(self):
        return self._sum_data

class CountAggregationData(BaseAggregationData):
    def __init__(self, count_data):
        super().__init__(count_data)
        self._count_data = count_data

    def add_sample(self, value):
        self._count_data = self._count_data + 1

    @property
    def count_data(self):
        return self._count_data

class MeanAggregationData(BaseAggregationData):
    def __init__(self, mean_data, count_data):
        super().__init__(mean_data)
        self._mean_data = mean_data
        self._count_data = count_data

    def add_sample(self, value):
        self._count_data = self._count_data + 1
        self._mean_data = (self._mean_data + (value - self._mean_data)) / self._count_data

    @property
    def mean_data(self):
        return self._mean_data

    @property
    def count_data(self):
        return self._count_data

class DistributionAggregationData(BaseAggregationData):
    def __init__(self, mean_data, count_data, min, max, sum_of_sqd_deviations, counts_per_bucket, bounds):
        super().__init__(mean_data)
        self._mean_data = mean_data
        self._count_data = count_data
        self.min = min
        self.max = max
        self.sum_of_sqd_deviations = sum_of_sqd_deviations
        self.counts_per_bucket = counts_per_bucket
        self.bounds = bucket_boundaries.BucketBoundaries(boundaries=bounds).boundaries

    @property
    def sum(self):
        return self._mean_data * self._count_data

    @property
    def variance(self):
        if self._count_data <= 1:
            return 0
        return self.sum_of_sqd_deviations / (self._count_data - 1)

    def add_sample(self, value):
        if value < self.min:
            self.min = value
        if value > self.max:
            self.max = value
        self._count_data += 1
        self.increment_bucket_count(value)

        if self._count_data == 1:
            self._mean_data = value
            return

        old_mean = self._mean_data
        self._mean_data = self._mean_data + (value - self._mean_data) / self._count_data
        self.sum_of_sqd_deviations = self.sum_of_sqd_deviations + (value - old_mean) * (value - self._mean_data)

    def increment_bucket_count(self, value):
        if len(self.bounds) == 0:
            self.counts_per_bucket[0] += 1
            return

        for i, b in self.bounds:
            if value < b:
                self.counts_per_bucket[i] += 1
                return

        self.counts_per_bucket[len(self.bounds)] += 1
