import networkx as nx
from ._internal import *

def draw(src, pos=None, ax=None, iterations=2, **layout_args):
    layout_args["iterations"] = iterations 
    g = src if (not isinstance(src, FlangeTree)) else src()

    if pos is None:
        pos=nx.spectral_layout(g)
        pos=nx.spring_layout(g, pos=pos, **layout_args)


    color_map = {"node": "r", "link": "b"}
    types = nx.get_node_attributes(g, "_type")
    colors = [color_map.get(types[node], "k") 
              for node in g.nodes()]

    labels = {node: node if types[node] is "node" else ""
              for node in g.nodes()}

    sizes = [300 if types[node] is "node" else 100
             for node in g.nodes()]

    nx.draw(g, pos=pos, ax=ax, node_size=sizes, node_color=colors)
    nx.draw_networkx_labels(g, labels=labels, pos=pos, ax=ax)

