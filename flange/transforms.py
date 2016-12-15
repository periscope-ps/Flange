import networkx as nx
from itertools import chain

from ._internal import FlangeTree, autotree


@autotree("test")
def select(self, graph): return test(graph)

class op(FlangeTree):
    def __init__(self, fn, *args):
        self.fn = fn
        self.curried = args

    def __call__(self, final):
        args = [x for x in self.curried]
        args.append(final)
        return fn.call(*all_args)

@autotree("att_id", default=None)
def att(self, graph):
    def _att(self, graph, vertex_id):
        try:
            return nx.get_vertex_attributes(graph, vertex_id)[self.att_id]
        except:
            return self.default
        
    return [self._att(graph, vertex_id) for vertex_id in graph.vertices()]


@autotree("predicate", label="*")
def collect(self, graph):
    """Gather verteices that pass a predcate into a hyper-vertex.
    
    predicate -- Return a list of vertex names to compress together
    label -- Name for the vertex representing all combined vertices
    
    TODO: Put edge data on to indicate the original vertex vertices
    TODO: Deal with edge properties (are they copied?  aggregated? modified?)
    """

    group_vertices = self.predicate(graph)
    stable_vertices = [vertex for vertex in graph.vertices() if vertex not in group_vertices]
    
    synth = graph.subgraph(stable_vertices)
    synth.add_vertex(self.label)
    
    outbound = list(graph.out_edges_iter(group_vertices))
    inbound = list(graph.in_edges_iter(group_vertices))

    for (start, end) in inbound:
        if not synth.has_edge(start, self.label) \
            and start not in group_vertices:
            synth.add_edge(start, self.label, **graph.get_edge_data(start, end))

    for (start, end) in outbound:
        if not synth.has_edge(self.label, end) \
            and end not in group_vertices:
            synth.add_edge(self.label, end, **graph.get_edge_data(start, end))

    return synth

@autotree()
def vertices(self, graph):
    """Return the vertices of a graph.
    TODO: Convert 'vertices' to an instance of something...so you can use it like 'vertices' instead of 'vertices()'
    """
    return graph.vertices()

@autotree("val")
def startswith(self, names):
    "Passed a list, returns all xs where x.startswith(val) is true."
    return [name for name in names if name.startswith(self.val)] 

@autotree("att", "test")
def all_att(self,  g): 
    """
    Return the subgraph containing only vertices with the given attribute/value pair.
    Test is a function to evaluate with 

    TODO: Generalize so the test can take a whole dictionary, not just a single attribute value
    """

    if callable(self.test):
        verts = [v for v in g.vertices() if self.test(g.vertex[v][self.att])]
    else:
        verts = [v for v in g.vertices() if g.vertex[v][self.att] == self.test]

    return g.subgraph(verts)


@autotree("op", external=True)
def neighbors(self, graph):
    """Executes the op on the graph, then re-inserts the node or link 
    verticies from the original graph and related edges.  

    This makes it easy to (for example) filter to nodes with a given name
    while keeping the connectivity information.

    op -- Operation to select verticies with
    external -- Keep link-verticies with only one connection in the subgraph?
                Such verticies point to some node that is *external* to the subgraph,
                thus the name.  Default is true.
    """

    selected = self.op(graph)
    outbound = chain(*[graph.successors(v) for v in selected.vertices()])
    inbound = chain(*[graph.predecessors(v) for v in selected.vertices()])
    
    subgraph = graph.subgraph(chain(inbound, outbound, selected.vertices()))
    if not self.external:
        vertices = [v for v in subgraph.vertices() 
                    if isnode(v, subgraph)
                       or len(all_edges(v, subgraph)) > 1]
        subgraph = graph.subgraph(vertices)
        
    return subgraph


nodes = all_att("_type", "node")  #Return a graph of just the nodes vertices
links = all_att("_type", "link")  #Return a graph of just the link vertices 


def islink(v, g):
    "Convenience methods to check if a vertex represents a network node"
    try:
        return g.vertex[v]["_type"] == "link"
    except:
        return False

def isnode(v, g):
    "Convenience methods to check if a vertex represents a network node"
    try:
        return g.vertex[v]["_type"] == "node"
    except:
        return False

def all_edges(v, g):
    "Convenience method to get inbound and outbound edges related to a vertex"
    return list(chain(g.out_edges(v), g.in_edges(v)))

@autotree("att", "val")
def set_att(self, graph, *, inplace=False):
    """Set an attribute on all vertices in a graph,

    att -- attribute to set
    val -- value to set to
    inplace -- Set true to mutate graph (otherwise makes a copy). Default is False.
    """
    g = graph.copy() if not inplace else graph
    nx.set_vertex_attributes(g, self.att, self.val)
    return g

@autotree("predicate")
def sub(self, graph):
    "TODO: Extend predicate to include lists and test with 'in'"
    if callable(self.predicate):
        vertices = [v for v in graph.vertices()
                    if self.predicate(v)]
    else:
        vertices = self.predicate

    return graph.subgraph(vertices)

