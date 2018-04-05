class BaseAggregationData(object):
    def __init__(self, aggregation_data):
        self.aggregation_data = aggregation_data

class SumAggregationDataFloat(BaseAggregationData):
    def __init__(self, sum_data):
        super().__init__(sum_data)
        self.sum = sum_data

    def add_sample(self, value):
        self.sum = self.sum + value

    def get_sum(self):
        return self.sum

class CountAggregationData(BaseAggregationData):
    def __init__(self, count_data):
        super().__init__(count_data)
        self.count = count_data

    def add_sample(self, value):
        self.count = self.count + 1

    def get_count(self):
        return self.count

class MeanAggregationData(BaseAggregationData):
    def __init__(self, mean_data, count_data):
        super().__init__(mean_data)
        self.mean = mean_data
        self.count = count_data

    def add_sample(self, value):
        self.count = self.count + 1
        self.mean = (self.mean * value) / self.count

    def get_mean(self):
        return self.mean

    def get_count(self):
        return self.count

class DistributionAggregationData(BaseAggregationData):
    def __init__(self, mean_data, count_data, min, max, sum_of_sqd_deviations, counts_per_bucket, bounds):
        super().__init__(mean_data)
        self.mean = mean_data
        self.count = count_data
        self.min = min
        self.max = max
        self.sum_of_sqd_deviations = sum_of_sqd_deviations
        self.counts_per_bucket = counts_per_bucket
        self.bounds = bounds

    def get_sum(self):
        return self.mean * self.count

    def get_variance(self):
        if self.count <= 1:
            return 0
        return self.sum_of_sqd_deviations / (self.count - 1)

    def add_sample(self, value):
        if value < self.min:
            self.min = value
        if value > self.max:
            self.max = value
        self.count += 1
        self.increment_bucket_count(value)

        if self.count == 1:
            self.mean = value
            return

        old_mean = self.mean
        self.mean = self.mean + (value-self.mean)/self.count
        self.sum_of_sqd_deviations = self.sum_of_sqd_deviations + (value - old_mean)*(value - self.mean)

    def increment_bucket_count(self, value):
        if len(self.bounds) == 0:
            self.counts_per_bucket[0] += 1
            return

        for i, b in self.bounds:
            if value < b:
                self.counts_per_bucket[i] += 1
                return

        self.counts_per_bucket[len(self.bounds)] += 1

