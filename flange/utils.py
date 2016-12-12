import networkx as nx
from ._internal import *
from .graphs import islink, isnode

def pick_labels(g, strategy):
    if strategy == "auto":
        links = [v for v in g.vertices() if islink(v,g)]
        nodes = [v for v in g.vertices() if isnode(v,g)]

        if len(links) > 0 and len(nodes) > 0 : 
            strategy = "nodes"
        elif len(links) > 0: 
            strategy = "links"
        else:
            strategy = "nodes"

    if strategy == "all":
        return {v: v for v in g.vertices()}
    
    if strategy == "nodes":
        return {v: v if not islink(v,g) else ""
                for v in g.vertices()}
    
    if strategy == "links": 
        return {v: v if not isnode(v,g) else ""
                for v in g.vertices()}

def draw(src, pos=None, ax=None, iterations=2, label='auto', **layout_args):
    layout_args["iterations"] = iterations 
    g = src if (not isinstance(src, FlangeTree)) else src()

    if pos is None:
        pos=nx.spectral_layout(g)
        pos=nx.spring_layout(g, pos=pos, **layout_args)

    def color(vertex):
        if isnode(vertex, g): return "r"
        if islink(vertex, g): return "b"
        return "w"

    types = nx.get_node_attributes(g, "_type")
    colors = [color(v) for v in g.vertices()] 

    labels = pick_labels(g, label)
    sizes = [300 if not islink(v, g) else 100
             for v in g.vertices()]

    nx.draw(g, pos=pos, ax=ax, node_size=sizes, node_color=colors)
    nx.draw_networkx_labels(g, labels=labels, pos=pos, ax=ax)
