class BucketBoundaries(object):

    def __init__(self, boundaries=None):
        self.boundaries = list(boundaries or [])

    def get_boundaries(self):
        return self.boundaries
