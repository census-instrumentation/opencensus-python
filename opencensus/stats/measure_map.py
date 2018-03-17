from opencensus.stats import measure
from opencensus.tags import tag_context

class MeasureMap(object):
    def __init__(self):
        ''' finish this '''

    def measure_int_put(self, key, value):
        tag_context.TagContext.put(tag_context.TagContext(measure.MeasureInt), key, value)

    def measure_float_put(self, key, value):
        tag_context.TagContext.put(tag_context.TagContext(measure.MeasureFloat), key, value)

    def record(self):
        ''' Finish This '''
