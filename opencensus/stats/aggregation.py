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
    def __init__(self, boundaries=None, distribution=None):
        '''self.boundaries = list(bucket_boundaries.BucketBoundaries(boundaries) or [])'''
        self.boundaries = bucket_boundaries.BucketBoundaries(boundaries)
        self.distribution = dict(distribution or {})

    def get_boundaries(self):
        return bucket_boundaries.BucketBoundaries.get_boundaries(self.boundaries)

    def get_distribution(self):
        return self.distribution
