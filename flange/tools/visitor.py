class Visitor(object):
    def apply(self, fn):
        return fn(self)

