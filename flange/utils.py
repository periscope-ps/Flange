import networkx as nx
import matplotlib.pyplot as plt
from collections import defaultdict

from ._internal import *
from .graphs import islink, isnode


def diff(old, new):
    """
    Computes the delta-graph between two nodes.
    Checks for changes in attributes or entity count (vertex added or deleted).

    TODO: Check for links added or deleted.
    
    old -- original graph
    new -- updated graph
    returns -- dictionary where keys are nodes that were changed
           and values are a description of the change
    """

    delta = defaultdict(list)
    def extend(key, val):
        "Create/extend a delta dictionary entry"
        entries = delta[key]
        entries.append(val)
 
    def cmp(dict1, dict2):
        "Compare to dictionaries"
        delta = {key:val for (key, val) in dict2.items()
                if dict2[key] is not dict1[key]}
        
        keys1 = set(dict1.keys())
        keys2 = set(dict2.keys())
        removed = {key:"prop removed" 
                   for key in keys1.difference(keys2)}
        added = {key:"prop added" 
                 for key in keys2.difference(keys1)}
        return {**delta, **removed, **added}
        
    
    for v in old.vertices():
        if v not in new.vertices():
            extend(v, ("deleted"))
            
    for v in new.vertices():
        if v not in old.vertices():
            extend(v, ("added"))
        else:
            changes = cmp(old.vertex[v], new.vertex[v])
            if changes:
                extend(v, ("props", changes))
            
    return delta 



def pick_labels(g, strategy):
    """Return the lables for a graph. 

    Strategies --
    * nodes: Label all verticies that represent graph nodes
    * links: Label all verticies that reprsent links
    * auto: Label nodes if there are any.  Label links otherwise
    """

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

def layout(graph, iterations=2, **layout_args):
    layout_args["iterations"] = iterations 

    pos=nx.spectral_layout(graph)
    pos=nx.spring_layout(graph, pos=pos, **layout_args)
    return pos


def draw(src, pos=None, ax=None, *, delta={}, label='auto', **layout_args):
    """Layout and draw a graph.

    src -- graph to layout
    pos -- Pre-computed layout
    ax -- matplotlib axis to draw on

    delta -- Graph diff output
    label -- Labeling strategy
    **layout_args -- Arguments passed through to the layout routine

    TODO: More detailed info on deltas

    """

    graph = src if (not isinstance(src, FlangeTree)) else src()

    pos = layout(graph, **layout_args) if pos is None else pos

    def color(vertex):
        if vertex in delta.keys(): return "#439B00"  #yellow: "#FFFF00"
        if isnode(vertex, graph): return "#F85565"
        if islink(vertex, graph): return "#4A7BBB"
        return "w"

    types = nx.get_node_attributes(graph, "_type")
    colors = [color(v) for v in graph.vertices()] 

    labels = pick_labels(graph, label)
    sizes = [300 if not islink(v, graph) else 100
             for v in graph.vertices()]

    nx.draw(graph, pos=pos, ax=ax, node_size=sizes, node_color=colors)
    nx.draw_networkx_labels(graph, labels=labels, pos=pos, ax=ax)


def show(flanglet, src, *, size=(8,10), **layout_args):
    "Draw a sequence of graphs to reprsent prcoessing" 

    graph = src if (not isinstance(src, FlangeTree)) else src()
    before = graph.copy()
    foci = flanglet.focus(before.copy())
    after = flanglet(before.copy())

    pos = layout(before, **layout_args)
    
    fig = plt.gcf()
    fig.set_figheight(size[0])
    fig.set_figwidth(size[1])
    
    cols = max(len(foci), 6)
    rows = 4
    ax_before = plt.subplot2grid((rows, cols), (0,0), colspan=cols//2, rowspan=3)
    ax_after = plt.subplot2grid((rows, cols), (0,cols//2), colspan=cols//2, rowspan=3)
   
    draw(before, pos=pos, ax=ax_before)

    for (i, sub) in enumerate(foci):
        ax_select = plt.subplot2grid((rows, cols), (3, i))
        draw(sub, pos=pos, ax=ax_select)

    delta = diff(before, after)
    draw(after, pos=pos, ax=ax_after, delta=delta)
    
    return fig
