from opencensus.stats.measure import BaseMeasure
from opencensus.stats.aggregation import DistributionAggregation


class View(object):
    def __init__(self, name, description, measure, aggregation):
        self.name = name
        self.description = description
        self.measure = BaseMeasure(measure.get_name(), measure.get_description(), measure.get_unit())
        self.aggregation = DistributionAggregation(aggregation.get_boundaries(), aggregation.get_distribution())

    def get_name(self):
        return self.name

    def get_description(self):
        return self.description

    def get_measure(self):
        return self.measure

    def get_aggregation(self):
        return self.aggregation
