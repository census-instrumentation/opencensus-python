class TagValue(object):
    max_value = 255

    def __init__(self, value):
        self.value = value

    def get_value(self, value):
        return value

    def is_value(self, value):
        if len(value) <= max_value:
            return True
        else:
            return False