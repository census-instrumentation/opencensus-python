from opencensus.stats import aggregation
from opencensus.stats import aggregation_data
from opencensus.stats import measure
from opencensus.stats import view
from opencensus.tags import tag_value
import time

class ViewData(object):
    def __init__(self, view, start, end, rows=None):
        self.view = view.view
        self.start = start
        self.end = end
        self.rows = dict({tag_value : aggregation_data} or {})

