from opencensus.tags import tag_key
from opencensus.tags import tag_value

class Tag(object):

    def __init__(self, key, value):
        self.key = tag_key.TagKey(key)
        self.value = tag_value.TagValue(value)

    def get_key(self):
        return self.key

    def get_value(self):
        return self.value



