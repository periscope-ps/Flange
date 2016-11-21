import networkx as nx
from ._internal import *

def draw(g, pos=None, ax=None):
    g = g if not isinstance(g, FlangeTree) else g()

    pos=nx.spring_layout(g) if pos is None else pos
    nx.draw(g, pos=pos, ax=ax)
    nx.draw_networkx_labels(g, pos=pos, ax=ax)

