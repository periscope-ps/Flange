class FlangeTree(object):
    def __call__(self, graph):
        "Process the passed graph;"
        raise RuntimeError("Must override the call method")

    def focus(self, graph):
        """What part of the graph is of interest to this rule.
        Should correspond to a partial evaluation of the call, 
        but not compute the end result, just the portion of interest
        """
        return None

class FlangeQuery(FlangeTree):
    "Call is the same as the focus"

    def __call__(self, graph):
        "Process the passed graph"
        raise RuntimeError("Must override the call method")

    def focus(self, graph): return self(graph)
