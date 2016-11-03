class FlangeTree(object):
    def __call__(self):
        raise RuntimeError("Must override the call method")

class ActionFailureError(RuntimeError):
    "Inidicates rule action was taken BUT the test still fails"
    pass

class NoValidChoice(RuntimeError):
    "Indicates that a search returned zero valid options."
    pass


def update(graph, values): pass


class place(FlangeTree):
    def __init__(self, mod, at, graph):
        self.mod = mod
        self.at = at
        self.graph = graph

    def __call__(self, *args):
        g = self.graph()
        position = self.at(g)
        g2 = self.mod(position, g)
        return g2
