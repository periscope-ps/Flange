
class GroupCondition(FlangeTree):
    def __init__(self, predicate, selector, graph):
        self.predicate = predicate
        self.selector = selector
        self.graph = graph

    def __call__(self, *args):
        g = self.graph()
        raw_items = self.selector(g)
        passing_items = [x for x in raw_items if self.predicate(x, g)]
        return self._test(passing_items, raw_items)

    def _test(self, passing_items, raw_items):
        raise Error("Not implemented")

class exists(GroupCondition):
    def _test(self,  passing_items, raw_items):
        return len(passing_items) > 0

class exactlyOne(GroupCondition):
    def _test(self, passing_items, raw_items):
        return len(passing_items) == 1

class all(GroupCondition):
    def _test(self, passing_items, raw_items):
        return len(passing_items) == len(raw_items)

class most(GroupCondition):
    def _test(self, passing_items, raw_items):
        return len(passing_items) >= len(raw_items)//2
