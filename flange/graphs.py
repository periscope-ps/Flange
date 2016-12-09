from unis.models import *
from unis.runtime import Runtime
import networkx as nx
from itertools import chain
from functools import reduce

from ._internal import FlangeTree, autotree

class unis(FlangeTree):
    "Retrieves a graph from a UNIS server."
    default_unis = "http://192.168.100.200:8888"
    _runtime_cache = {}

    def __init__(self, ref="*", source=default_unis):
        self.source = source
        self.ref = ref

    def __call__(self):
        #TODO: This is a bare-bones buildling of the graph model; make it better
        rt = self._runtime()
        topology = rt

        if not self.ref == "*": 
            try:
                topology= list(rt.topologies.where({"id": self.ref}))[0]
            except IndexError:
                raise ValueError("No topology named '{0}' found in UNIS instance {1}".format(self.ref, self.source)) from None 
            

        g = nx.DiGraph() 
        for port in topology.ports:
            #HACK: Grabbing __dict__ probably won't work for long...
            g.add_vertex(port.id, **port.__dict__) 

        for link in topology.links:
            if not link.directed:
                g.add_edge(link.endpoints[0].id, link.endpoints[1], **link.__dict__)
                g.add_edge(link.endpoints[1].id, link.endpoints[2], **link.__dict__)
            else:
                g.add_edge(link.source.id, link.sink.id, **link.__dict__)

        return g

    def _runtime(self):
        return self.cached_connection(self.source)

    @classmethod
    def cached_connection(cls, source):
        rt = cls._runtime_cache.get(source, Runtime(source))
        cls._runtime_cache[source] = rt
        return rt


class graph(FlangeTree):
    linear = {"vertices": ["port1","port2","port3","port4"],
              "edges": [("port1", "port2"), ("port2", "port3"),("port3", "port4"),
                        ("port2", "port1"), ("port3", "port2"),("port4", "port3")]}

    ring = {"vertices": ["port1", "port2", "port3", "port4"],
            "edges": [("port1", "port2"), ("port2", "port3"),
                      ("port3", "port4"), ("port4", "port1")]}

    dynamic=[{"vertices": ["p1", "p2", "p3"], "edges": []},
             {"vertices": ["p1", "p2", "p3", "p4"], "edges": []},
             {"vertices": ["p1", "p2", "p3", "p4", "p5"], "edges": []},
             {"vertices": ["p1", "p2", "p3", "p4", "p5"], "edges": []},
             {"vertices": ["p1", "p2", "p3", "p4", "p5", "p6"], "edges": []}]

    ab_ring = {"vertices": ["A1", "A2", "A3", "A4", "A5", "B1", "B2", "B3"],
               "edges": [("A1", "A2"), ("A2", "A3"), ("A3", "B1"), 
                        ("B1", "A4"), 
                        ("A4", "B2"), ("B2", "B3"), ("B3", "A5"),
                        ("A5", "A1")]}

    layers = {"vertices": ["Z1", "A1", "A2", "A3", "B1", "B2", "C1", "C2", "D1"],
              "edges": [("Z1", "A1"), ("Z1", "A2"), ("Z1", "A3"),
                        ("A1", "Z1"), ("A2", "Z1"), ("A3", "Z1"),
                        ("A1", "B1"), ("A1", "B2"), ("A2", "B1"), ("A2", "B2"), ("A3", "B1"), ("A3", "B2"),
                        ("B1", "A1"), ("B2", "A1"), ("B1", "A2"), ("B2", "A2"), ("B1", "A3"), ("B2", "A3"),
                        ("B1", "C1"), ("B2", "C1"), ("B1", "C2"), ("B2", "C2"),
                        ("C1", "B1"), ("C1", "B2"), ("C2", "B1"), ("C2", "B2"),
                        ("C1", "D1"), ("C2", "D1"),
                        ("D1", "C1"), ("D1", "C2")]}

    def __init__(self, topology="linear", vertices=None, edges=None):
        self.dynamic=0

        if vertices or edges:
            self.topology = {"vertices": vertices if vertices else [],
                             "edges": edges if edges else []}
        else:
            try:
                self.topology = graph.__getattribute__(graph, topology)
            except AttributeError as e:
                raise ValueError("No pre-defined graph with name '{0}'".format(topology)) from None


    def __call__(self):
        try:
            topology = self.topology[self.dynamic]
            self.dynamic = (self.dynamic+1) % len(self.topology)
        except:
            topology = self.topology

        vertices = [(name, {"id": name, "_type": "node"}) 
                    for name in topology["vertices"]]
        vertices.extend([(vertex, {"id": vertex, "_type": "link"}) 
                         for vertex in topology["edges"]])
        edges = [((src, (src,dst)), ((src,dst), dst)) 
                 for (src, dst) in topology["edges"]]

        g = nx.DiGraph()

        g.add_vertices_from(vertices)
        g.add_edges_from(chain(*edges))
        self.graph = g
        return self.graph


class wrap(FlangeTree):
    "Wrap a reference to a graph"
    def __init__(self, g): self.g = g
    def __call__(self): return self.g


### Graph transformation operators
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
    
    def all_edges(v, g):
        return list(chain(g.out_edges(v), g.in_edges(v)))
    
    subgraph = graph.subgraph(chain(inbound, outbound, selected.vertices()))
    if not self.external:
        vertices = [v for v in subgraph.vertices() 
                    if subgraph.vertex[v]["_type"] == "node" \
                       or len(all_edges(v, subgraph)) > 1]
        subgraph = graph.subgraph(vertices)
        
    return subgraph


nodes = all_att("_type", "node")  #Return a graph of just the nodes vertices
links = all_att("_type", "link")  #Return a graph of just the link vertices 
