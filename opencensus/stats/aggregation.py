from opencensus.stats import bucket_boundaries

class BaseAggregation(object):
    def __init__(self, aggregation=None):
        self.aggregation = dict(aggregation or {})

    def get_aggregation(self):
        return self.aggregation

class SumAggregation(BaseAggregation):
    def __init__(self, instance):
        self.instance = instance

    def get_instance(self):
        return self.instance

class CountAggregation(BaseAggregation):
    def __init__(self, instance):
        self.instance = instance

    def get_instance(self):
        return self.instance

class MeanAggregation(BaseAggregation):
    def __init__(self, instance):
        self.instance = instance

    def get_instance(self):
        return self.instance

class DistributionAggregation(BaseAggregation):
    def __init__(self, bucket_boundaries, distribution=None):
        self.distribution = dict(distribution or {})
        self.bucket_boundaries = bucket_boundaries.BucketBoundaries(bucket_boundaries)

    def get_boundaries(self):
        return bucket_boundaries.BucketBoundaries.get_boundaries(self.bucket_boundaries)