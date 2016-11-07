import networkx as nx
from ._internal import *

def draw(g):
    g = g if not isinstance(g, FlangeTree) else g()

    pos=nx.spring_layout(g)
    nx.draw(g, pos=pos)
    nx.draw_networkx_labels(g, pos=pos)

