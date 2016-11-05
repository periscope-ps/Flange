import networkx as nx
import itertools
from ._internal import FlangeTree

def between(criteria, src_selector, dst_selector, graph):
    """Finds a path bewteen the source and target selector where each hop
       statisfies the given criteria.

    TODO: Convert to class/curried style
    TODO: handle multple sources or targets...
    TODO: Modify so it finds a set of paths that collectively satisfy the
            criteria instead of just one path that always does.  That way
            you can build a flow from A to B where no individual link is
            sufficient but combinations of links are.
    """

    try:
        s = next(filter(src_selector, g.nodes()))
        t = next(filter(dst_selector, g.nodes()))
    except StopIteration:
        raise NoValidChoice("Source or target set empty")

    allpaths = nx.all_simple_paths(graph, s, t)
    return allpaths


    nx.shortest_path(s, t)

    # Get all paths froms src to target
    # For each path, find a spot that matches criteria
    # Do something "smart" so you use a few spots as possible (so if paths intersect and the intersection matches, use it)
    # exclude SRC and target
    pass


class on(FlangeTree):
    """Returns a subgraph defined by the selector.  
    The implication is that all items in the subgraph will be modified
    """

    def __init__(self, selector):
        self.selector = selector

    def __call__(self, graph):
        selector = lambda x: self.selector(x, graph)
        nodes = list(filter(selector, graph.nodes()))
        synth = graph.subgraph(nodes)
        return synth

class around(FlangeTree):
    """Given a graph and a selector, returns a list of links that go in or out of the 
    selected nodes"""
    def __init__(self, selector):
        self.selector = selector

    def __call__(self, graph):
        selector = lambda x: self.selector(x,graph)
        nodes = list(filter(selector, graph.nodes())) ## TODO -- More complex query here
        outbound = graph.edges_iter(nodes)
        inbound = graph.edges_iter(nodes)
        return set(itertools.chain(outbound, inbound))

class near(FlangeTree):
    """Find a node that is topologically 'near' the selection and passes the criteria.

    * Nearness is topological nearness (based on BFS)
    * Criteria is a function that determines if a node passes the selection criteria

    TODO: Custom/pluggable nearness functions (such as BFS or custom weighting functions)
    """
    def __init__(self, criteria, selector):
        self.criteria = criteria
        self.selector = selector

    def __call__(self, graph):

        selector = lambda x: self.selector(x, graph)
        criteria = lambda x: self.criteria(x, graph)
        sources = list(filter(selector, graph.nodes()))

        def path_weight(path):
            # TODO: look up  weights in the graph
            return len(path)

        all_paths = {s:nx.shortest_path(graph, source=s) for s in sources}
        paths = [steps for (s, paths) in all_paths.items()
                       for (t, steps) in paths.items()]

        distances = [(path[-1], path_weight(path)) for path in paths if len(path) > 1]
        valid = list(filter(criteria, distances))
        if len(valid) == 0: raise NoValidChoice()

        preferred = min(valid, key=lambda e: e[1])

        return preferred[0]

class inside(flange.FlangeTree):
    """Given a graph and a selector, returns a list of links that make up the min cut
    
    TODO: Graph must have a clear "side-id-ness" to it to work...  
          ###Source and ###Sink cannot both link to the same node.
    """
    def __init__(self, selector):
        self.selector=selector

    def __call__(self, graph):
        selector = lambda x: self.selector(x, graph)
        nodes = list(filter(selector, graph.nodes())) ## TODO -- More complex query here
        synth = graph.subgraph(nodes) ## Get the subgraph indicated by the selector
        nx.set_edge_attributes(synth, 'capacity', 1)

        print("all nodes", nodes)
        print("init synth nodes:", synth.nodes())
        print("init synth edges:", synth.edges())
        outbound = list(graph.out_edges_iter(nodes))
        inbound = list(graph.in_edges_iter(nodes))
        print(inbound)
        print(outbound)

        src = "##SOURCE##"
        synth.add_node(src)
        for edge in inbound:
            if not synth.has_edge(*edge):
                synth.add_edge(src, edge[1], capacity=10)

        sink = "##SINK##"
        synth.add_node(sink)
        for edge in outbound:
            if not synth.has_edge(*edge):
                synth.add_edge(edge[0], sink, capacity=10)

        draw(synth)
        print("synth edges:", synth.edges())
        cut_value, partition = nx.minimum_cut(synth, s=src, t=sink, capacity='capacity')
        reachable, non_reachable = partition

        cutset = set()
        for u, nbrs in ((n, synth[n]) for n in reachable):
            cutset.update((u, v) for v in nbrs if v in non_reachable)
            cut_value == sum(synth.edge[u][v]['capacity'] for (u, v) in cutset)


        return cutset
