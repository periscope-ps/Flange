from ._internal import *


#TODO: write update...
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
