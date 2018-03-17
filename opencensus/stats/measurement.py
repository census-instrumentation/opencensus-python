from opencensus.stats import measure

class Measurement(object):
    def __init__(self, measure, value):
        self.measure = measure.Measure(measure)
        self.value = value

    def get_measure(self):
        return self.measure.Measure

class MeasurementInt(Measurement):
    def __init__(self, measure, value):
        super().__init__(measure, value)

class MeasurementFloat(Measurement):
    def __init__(self, measure, value):
        super().__init__(measure, value)