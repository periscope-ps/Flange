import networkx as nx
import itertools
from ._internal import FlangeTree

class between(FlangeTree):
    def __init__(self, criteria, src_selector, dst_selector):
        self.criteria = criteria
        self.src_selector = src_selector
        self.dst_selector = dst_selector

    def __call__(self, graph):
        """Finds a path bewteen the source and target selector where each hop
           statisfies the given criteria.

        TODO: handle multple sources or targets...
        TODO: Modify so it finds a set of paths that collectively satisfy the
                criteria instead of just one path that always does.  That way
                you can build a flow from A to B where no individual link is
                sufficient but combinations of links are.
        """

        paths = self.focus(graph)
        ranked = sorted(paths, self.criteria)
        
        try:
            return ranked[0] 
        except IndexError:
            raise NoValidChoice("No paths found from selected source/target node(s)", )


    def focus(self, graph):
        try:
            s = next(filter(self.src_selector, graph.nodes()))
            t = next(filter(self.dst_selector, graph.nodes()))
        except StopIteration:
            raise NoValidChoice("Source or target set empty")

        allpaths = nx.all_simple_paths(graph, s, t)

        return allpaths


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

    def focus(self, graph):
        return self.selector(graph)

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
    
    def focus(self, graph):
        return self.selector(graph)

class near(FlangeTree):
    """Find a node that is topologically 'near' the selection and passes the criteria.

    * Nearness is topological nearness (based on BFS)
    * Criteria is a function that determines if a node passes the selection criteria

    TODO: Custom/pluggable nearness functions (such as BFS or custom weighting functions)
    TODO: Mechanism for return mulitple results
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
    
    def focus(self, graph):
        return self.selector(graph)

class inside(FlangeTree):
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

        outbound = list(graph.out_edges_iter(nodes))
        inbound = list(graph.in_edges_iter(nodes))

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

        cut_value, partition = nx.minimum_cut(synth, s=src, t=sink, capacity='capacity')
        reachable, non_reachable = partition

        cutset = set()
        for u, nbrs in ((n, synth[n]) for n in reachable):
            cutset.update((u, v) for v in nbrs if v in non_reachable)
            cut_value == sum(synth.edge[u][v]['capacity'] for (u, v) in cutset)


        return cutset

    def focus(self, graph):
        return self.selector(graph)
