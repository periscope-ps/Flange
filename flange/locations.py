import networkx as nx
import itertools
from ._internal import FlangeTree
from .errors import NoValidChoice
from .graphs import islink

class between(FlangeTree):
    def __init__(self, src_selector, dst_selector, criteria=lambda x: 0):
        self.src_selector = src_selector
        self.dst_selector = dst_selector
        self.criteria = criteria

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
        ranked = sorted(paths, key=self.criteria)
        try:
            return graph.subgraph(ranked[0][1:-1])
        except IndexError:
            raise NoValidChoice("No paths found from selected source/target vertex/vertices", )


    def focus(self, graph):
        #TODO: Extend to multiple source/targets
        s = self.src_selector(graph).vertices()[0]
        t = self.dst_selector(graph).vertices()[0]

        allpaths = nx.all_simple_paths(graph, s, t)

        return allpaths


class on(FlangeTree):
    "Returns a subgraph defined by the selector."

    def __init__(self, selector):
        self.selector = selector

    def __call__(self, graph):
        vertices = self.selector(graph)
        synth = graph.subgraph(vertices)
        return synth

    def focus(self, graph):
        return self.selector(graph)

class around(FlangeTree):
    """Given a graph and a selector, returns a subgraph that is just the link vertices
    that go in to or out of the selected (probably node) vertices.
    """
    def __init__(self, selector):
        self.selector = selector

    def __call__(self, graph):
        selected = self.selector(graph)
        
        outbound = itertools.chain(*[graph.successors(v) for v in selected.vertices()])
        inbound = itertools.chain(*[graph.predecessors(v) for v in selected.vertices()])
        return graph.subgraph(itertools.chain(inbound, outbound))
    
    def focus(self, graph):
        return self.selector(graph)

class near(FlangeTree):
    """Find a vertex that is topologically 'near' the selection and passes the criteria.

    * Nearness is topological nearness (based on BFS)
    * Criteria is a function that determines if a vertex passes the selection criteria

    TODO: Custom/pluggable nearness functions (such as BFS or custom weighting functions)
    TODO: Mechanism for return mulitple results
    """
    def __init__(self, criteria, selector):
        self.criteria = criteria
        self.selector = selector

    def __call__(self, graph):
        selector = lambda x: self.selector(x, graph)
        sources = list(filter(selector, graph.vertices()))

        def path_weight(path):
            # TODO: look up  weights in the graph using vertex attributes
            return len(path)

        all_paths = {s:nx.shortest_path(graph, source=s) for s in sources}
        paths = [steps for (s, paths) in all_paths.items()
                       for (t, steps) in paths.items()]

        distances = [(path[-1], path_weight(path)) for path in paths if len(path) > 1]

        def passes_criteria(path):
            path_graph = graph.subgraph(path[-1])
            return len(self.criteria(path_graph)) > 0  #Passes

        valid = [(path, weight) 
                 for (path, weight) in distances
                 if passes_criteria(path)]
        
        if len(valid) == 0: raise NoValidChoice()

        preferred = min(valid, key=lambda e: e[1])
        return graph.subgraph(preferred[0][-1])
    
    def focus(self, graph):
        return self.selector(graph)
    

class across(FlangeTree):
    """Given a graph and a selector, returns a list of links that make up the min cut

    src_selector -- Source nodes for the flow
    dst_selector -- Destination nodes for the flow
              
    TODO: Use real link capacity figures (from the graph...)
    TODO: Auto-generate capacity (the hard-coded 10 is a HORRIBLE default)
    TODO: Is there a variant the returns nodes instead of links?  Does that make sense?
    """
    def __init__(self, src_selector, dst_selector, capacity=10):
        self.src_selector = src_selector
        self.dst_selector = dst_selector
        self.capacity=capacity

    def __call__(self, graph):
        sources = self.src_selector(graph)
        dests = self.dst_selector(graph)
        
        if len(sources) == 0 or len(dests) == 0:
            raise NoValidChoice("Source or destination set is empty")
            
        if not set(sources.vertices()).isdisjoint(set(dests.vertices())):
            raise NoValidChoice("Source and Sink verticies are NOT disjoint, cannot find cut across")
            
        synth = graph.copy()
        nx.set_edge_attributes(synth, 'capacity', 1)

        src = sources.vertices()[0]
        if len(sources) > 1:
            src = "##SOURCE##"
            synth.add_vertex(src)
            for v in sources:
                synth.add_edge(src, v, capacity=self.capacity)  
                

        sink = dests.vertices()[0]
        if len(dests) > 1:
            sink = "##SINK##"
            synth.add_vertex(sink)
            for v in dests:
                synth.add_edge(v, sink, capacity=self.capacity)  
            
        cut_value, partition = nx.minimum_cut(synth, s=src, t=sink, capacity='capacity')
        side_a, side_b = partition
        
        links = [v for v in side_a if islink(v, graph)]
        if len(links) == 0:
            swap = side_a
            side_a = side_b
            side_b = swap
            links = [v for v in side_a if islink(v)]
            
        cutset = [v for v in links 
                  if (v[0] in side_a and v[1] in side_b) \
                      or (v[0] in side_b and v[1] in side_a)]
        
        return graph.subgraph(cutset)

    def focus(self, graph):
        return self.selector(graph)
