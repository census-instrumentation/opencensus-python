from opencensus.tags import tag_key
from opencensus.tags import tag_value

class Tag(object):

    def __init__(self, key, value):
        self.key = tag_key.TagKey(key)
        self.value = tag_value.TagValue(value)

    def get_key(self, key):
        return tag_key.TagKey.get_name(key, None)

    def get_value(self, value):
        return tag_value.TagValue.get_value(value, None)



