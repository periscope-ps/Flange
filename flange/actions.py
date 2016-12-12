from ._internal import *


#TODO: write update...
def update(graph, values): pass

@autotree("mod", "at")
def place(self, graph):
    "Put information at a specific place on the graph"

    position = self.at(graph)
    g2 = self.mod(position)
    return g2

