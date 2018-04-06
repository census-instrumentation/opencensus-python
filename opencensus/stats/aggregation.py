from opencensus.stats import bucket_boundaries
from opencensus.stats import aggregation_data

class BaseAggregation(object):
    def __init__(self, aggregation_type=None, buckets=None):
        if aggregation_type is not None:
            self.aggregation_type = aggregation_type

        if buckets is not None:
            self.buckets = buckets

    def get_aggregation(self):
        return self.aggregation_type

class SumAggregation(BaseAggregation):
    def __init__(self, sum=None, aggregation_type="sum"):
        super().__init__(aggregation_type)
        self.aggregation_type = aggregation_type
        if sum is not None:
            self.sum = aggregation_data.SumAggregationDataFloat(sum)
        else:
            self.sum = aggregation_data.SumAggregationDataFloat(0)

    def get_aggregation(self):
        return self.aggregation_type

    def get_sum(self):
        return self.sum

class CountAggregation(BaseAggregation):
    def __init__(self, count=None, aggregation_type="count"):
        super().__init__(aggregation_type)
        self.aggregation_type = aggregation_type
        if count is not None:
            self.count = aggregation_data.CountAggregationData(count)
        else:
            self.count = aggregation_data.CountAggregationData(0)

    def get_aggregation(self):
        return self.aggregation_type

    def get_count(self):
        return self.count

class MeanAggregation(BaseAggregation):
    def __init__(self, mean=None, aggregation_type="mean"):
        super().__init__(aggregation_type)
        self.aggregation_type = aggregation_type
        if mean is not None:
            self.mean = aggregation_data.MeanAggregationData(mean)
        else:
            self.mean = aggregation_data.MeanAggregationData(0)

    def get_aggregation(self):
        return self.aggregation_type

    def get_mean(self):
        return self.mean

class DistributionAggregation(BaseAggregation):
    def __init__(self, boundaries=None, distribution=None, aggregation_type="distribution"):
        super().__init__(aggregation_type, boundaries)
        self.aggregation_type = aggregation_type
        '''self.boundaries = list(bucket_boundaries.BucketBoundaries(boundaries) or [])'''
        self.boundaries = bucket_boundaries.BucketBoundaries(boundaries)
        self.distribution = dict(distribution or {})

    def get_aggregation(self):
        return self.aggregation_type

    def get_boundaries(self):
        return bucket_boundaries.BucketBoundaries.get_boundaries(self.boundaries)

    def get_distribution(self):
        return self.distribution
