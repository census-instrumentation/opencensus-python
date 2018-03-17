class BaseAggregationData(object):
    def __init__(self, aggregation_data=None):
        self.aggregation_data = dict(aggregation_data or {})

class SumAggregationDataInt(BaseAggregationData):
    def __init__(self, sum):
        self.sum = sum

    def get_sum(self):
        return self.sum

class SumAggregationDataFloat(BaseAggregationData):
    def __init__(self, sum):
        self.sum = sum

    def get_sum(self):
        return self.sum

class CountAggregationData(BaseAggregationData):
    def __init__(self, count):
        self.count = count

    def get_count(self):
        return self.count

class MeanAggregationData(BaseAggregationData):
    def __init__(self, mean, count):
        self.mean = mean
        self.count = count

    def get_mean(self):
        return self.mean

    def get_count(self):
        return self.count

class DistributionAggregationData(BaseAggregationData):
    def __init__(self, mean, count, min, max, sum_of_sqd_deviations, counts_per_bucket):
        self.mean = mean
        self.count = count
        self.min = min
        self.max = max
        self.sum_of_sqd_deviations = sum_of_sqd_deviations
        self.counts_per_bucket = counts_per_bucket
