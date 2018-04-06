from opencensus.tags import tag
from opencensus.tags import tag_key
from opencensus.tags import tag_value

class TagMap(object):

    def __init__(self, tags=None, map=None):
        if map is None:
            self.map = {}
        else:
            self.map = map
        if tags is not None:
            self.tags = {}
            for tag.Tag in tags:
                self.tags[] = tag.tag_value
        else:
            self.tags = {}

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

    def tag_key_exits(self, key):
        if key in self.map:
            return True
        else:
            return False

    def get_value(self, key):
        if key in self.map:
            return self.map[key]
        else:
            return "key is not in map"


