from opencensus.tags import tag_key
from opencensus.tags import tag_value


class TagContext(object):

    def __init__(self, tags=None):
        self.tags = dict(tags or {})

    def put(self, key, value):
        self.tags[key] = value

    def remove(self, key):
        self.tags.pop(key, None)

    def get_tags(self):
        return self.tags

    def get_tag_value(self, key):
        if key in self.tags:
            return self.tags[key]

