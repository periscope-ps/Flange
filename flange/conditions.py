from ._internal import FlangeTree

class GroupCondition(FlangeTree):
    def __init__(self, predicate, selector):
        self.predicate = predicate
        self.selector = selector

    def __call__(self, graph):
        raw_items = self.selector(graph)
        passing_items = [x for x in raw_items if self.predicate(x, graph)]
        return self.test(passing_items, raw_items)

    def test(self, passing_items, raw_items):
        raise Error("Not implemented")

    def focus(self, graph):
        return self.selector(graph)

class exists(GroupCondition):
    def test(self,  passing_items, raw_items):
        return len(passing_items) > 0

class exactlyOne(GroupCondition):
    def test(self, passing_items, raw_items):
        return len(passing_items) == 1

class all(GroupCondition):
    def test(self, passing_items, raw_items):
        return len(passing_items) == len(raw_items)

class most(GroupCondition):
    def test(self, passing_items, raw_items):
        return len(passing_items) >= len(raw_items)//2
