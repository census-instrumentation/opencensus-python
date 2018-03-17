class BaseMeasure(object):

    def __init__(self, name, description, unit=None):
        self.name = name
        self.description = description
        self.unit = unit

    def get_name(self):
        return self.name

    def get_description(self):
        return self.description

    def get_unit(self):
        return self.unit


class MeasureInt(BaseMeasure):
    def __init__(self, name, description, unit=None):
        super().__init__(name, description, unit)


class MeasureFloat(BaseMeasure):
    def __init__(self, name, description, unit=None):
        super().__init__(name, description, unit)