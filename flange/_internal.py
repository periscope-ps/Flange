class FlangeTree(object):

    def __call__(self, graph):
        "Process the passed graph;"
        raise RuntimeError("Must override the call method")

    def focus(self, graph):
        """What part of the graph is of interest to this rule.
        Should correspond to a partial evaluation of the call, 
        but not compute the end result, just the portion of interest

        Default implementation is a call to the regular "__call__" method,
        since that should be stateless...
        """
        return self(graph)

    def __rshift__(self, other):
        "Chaining operator.  Calls self, then passes result to call of other"
        return lambda arg: other(self(arg))

