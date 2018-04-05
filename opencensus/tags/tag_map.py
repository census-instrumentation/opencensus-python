from opencensus.tags import tag

class TagMap(object):

    def __init__(self, tags=None):
        self.tags = dict(tags or {})
        self.map = {}
        for tag.Tag in self.tags:
            self.map[tag.tag_key] = tag.tag_value

    def insert(self, key, value):
        if key in self.map:
            return
        else:
            self.map[key] = value

    def delete(self, key):
        self.map.pop(key, None)

    def update(self, key, value):
        if key in self.map:
            self.map[key] = value

    def value(self, key):
        if key in self.map:
            return self.map[key]
        else:
            return "key is not in map"


