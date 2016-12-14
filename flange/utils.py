import networkx as nx
from ._internal import *
from .graphs import islink, isnode


from collections import defaultdict
def delta(old, new):
    """
    Computes the delta between two nodes.
    Delta is a change in attributes or entity count (vertex added or deleted)
    or structure (links added or deleted).
    
    old -- original graph
    new -- updated graph
    returns -- dictionary where keys are nodes that were changed
           and values are a description of the change
    """
    
    delta = defaultdict(list)
    def extend(key, val):
        entries = delta[key]
        entries.append(val)
        
    def cmp(dict1, dict2):
        diff = {key:val for (key, val) in dict2.items()
                if dict2[key] is not dict1[key]}
        
        keys1 = set(dict1.keys())
        keys2 = set(dict2.keys())
        removed = {key:"prop removed" 
                   for key in keys1.difference(keys2)}
        added = {key:"prop added" 
                 for key in keys2.difference(keys1)}
        return {**diff, **removed, **added}
        
    
    for v in old.vertices():
        if v not in new.vertices():
            extend(v, ("deleted"))
            
    for v in new.vertices():
        if v not in old.vertices():
            extend(v, ("added"))
        else:
            diff = cmp(old.vertex[v], new.vertex[v])
            if diff:
                extend(v, ("props", diff))
            
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

def draw(src, pos=None, ax=None, *, delta=[], iterations=2, label='auto', **layout_args):
    "Layout and draw a graph."

    layout_args["iterations"] = iterations 
    g = src if (not isinstance(src, FlangeTree)) else src()

    if pos is None:
        pos=nx.spectral_layout(g)
        pos=nx.spring_layout(g, pos=pos, **layout_args)

    def color(vertex):
        if vertex in delta: return "#439B00"  #yellow: "#FFFF00"
        if isnode(vertex, g): return "#F85565"
        if islink(vertex, g): return "#4A7BBB"
        return "w"

    types = nx.get_node_attributes(g, "_type")
    colors = [color(v) for v in g.vertices()] 

    labels = pick_labels(g, label)
    sizes = [300 if not islink(v, g) else 100
             for v in g.vertices()]

    nx.draw(g, pos=pos, ax=ax, node_size=sizes, node_color=colors)
    nx.draw_networkx_labels(g, labels=labels, pos=pos, ax=ax)

def show(flanglet, graph, *, size=(8,10)):
    "Draw a sequence of graphs to reprsent prcoessing" 

    before = graph().copy()
    foci = flanglet.focus(before.copy())
    after = flanglet(before.copy())

    pos = nx.spring_layout(before)
    
    fig = plt.gcf()
    fig.set_figheight(size[0])
    fig.set_figwidth(size[1])
    
    cols = max(len(foci), 6)
    rows = 4
    ax_before = plt.subplot2grid((rows, cols), (0,0), colspan=cols//2, rowspan=3)
    ax_after = plt.subplot2grid((rows, cols), (0,cols//2), colspan=cols//2, rowspan=3)
        
    nx.draw(before, pos=pos, ax=ax_before)
    nx.draw_networkx_labels(before, pos=pos, ax=ax_before)

    for (i, sub) in enumerate(foci):
        ax_select = plt.subplot2grid((rows, cols), (3, i))
        nx.draw(sub, pos=pos, ax=ax_select)
        nx.draw_networkx_labels(sub, pos=pos, ax=ax_select)

    nx.draw(after, pos=pos, ax=ax_after)
    nx.draw_networkx_labels(after, pos=pos, ax=ax_after)
    
    return fig



