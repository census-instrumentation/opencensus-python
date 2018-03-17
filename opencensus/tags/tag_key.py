class TagKey(object):

    max_length = 255

    def __init__(self, name):
        self.name = name

    def get_name(self, name):
        return name

    def is_valid(self, name):
        if len(name) > 0 and len(name) <= max_length:
            return True
        else:
            return False



