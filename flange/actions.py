from ._internal import *

def update(original, updates):
    """Push a set of changed from 'updates' in to the original

    TODO: Handle vertex/edge deletion (path de-allocation, for example)
    """

    updated = original.copy()

    for v in updates.vertices():
        if v not in updated.vertices():
            updated.add_vertex(v)

        for (att, val) in updates.vertex[v].items():
            updated.vertex[v][att] = val


    return updated


@autotree("mod", "at")
def place(self, graph):
    "Put information at a specific place on the graph"

    position = self.at(graph)
    g2 = self.mod(position)
    return update(graph, g2)
