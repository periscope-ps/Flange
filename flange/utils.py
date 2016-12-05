import networkx as nx
from ._internal import *

def draw(g, pos=None, ax=None, **layout_args):
    color_map = {"node": "r", "link": "b"}
    g = g if not isinstance(g, FlangeTree) else g()
    pos=nx.spring_layout(g, **layout_args) if pos is None else pos

    types = nx.get_node_attributes(g, "_type")
    colors = [color_map.get(types[node], "k") 
              for node in g.nodes()]

    nx.draw(g, pos=pos, ax=ax, node_color=colors)
    nx.draw_networkx_labels(g, pos=pos, ax=ax)

