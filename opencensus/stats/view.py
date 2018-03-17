from opencensus.stats import measure
from opencensus.stats import aggregation
from opencensus.tags import tag_key

class View(object):
    def __init__(self, name, description, measure, aggregation, columns):
        self.name = name
        self.description = description
        self.measure = measure.Measure(self.measure)
        self.aggregation = aggregation.BaseAggregation(self.aggregation)
        self.columns = columns[tag_key]

    def get_name(self):
        return self.name

    def get_description(self):
        return self.description

    def get_measure(self):
        return measure.Measure.get_description(self.measure)

    def get_aggregation(self):
        return aggregation.BaseAggregation.get_aggregation(self.aggregation)

    def get_columns(self):
        return self.columns