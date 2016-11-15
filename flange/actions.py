from ._internal import *


#TODO: write update...
def update(graph, values): pass


class place(FlangeTree):
    def __init__(self, mod, at):
        self.mod = mod
        self.at = at

    def __call__(self, graph):
        position = self.at(graph)
        g2 = self.mod(position, graph)
        return g2
