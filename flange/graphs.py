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
            g.add_node(port.id, **port.__dict__) 

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
        g.add_nodes_from(vertices)
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
    def _att(self, graph, node_id):
        try:
            return nx.get_node_attributes(graph, node_id)[self.att_id]
        except:
            return self.default
        
    return [self._att(graph, node_id) for node_id in graph.nodes()]


@autotree("predicate", label="*")
def collect(self, graph):
    """Gather nodes that pass a predcate into a hyper-node.
    
    predicate -- Return a list of node names to compress together
    label -- Name for the node representing all combined nodes
    
    TODO: Put edge data on to indicate the original node nodes
    TODO: Deal with edge properties (are they copied?  aggregated? modified?)
    """

    group_nodes = self.predicate(graph)
    stable_nodes = [node for node in graph.nodes() if node not in group_nodes]
    
    synth = graph.subgraph(stable_nodes)
    synth.add_node(self.label)
    
    outbound = list(graph.out_edges_iter(group_nodes))
    inbound = list(graph.in_edges_iter(group_nodes))

    for (start, end) in inbound:
        if not synth.has_edge(start, self.label) \
            and start not in group_nodes:
            synth.add_edge(start, self.label, **graph.get_edge_data(start, end))

    for (start, end) in outbound:
        if not synth.has_edge(self.label, end) \
            and end not in group_nodes:
            synth.add_edge(self.label, end, **graph.get_edge_data(start, end))

    return synth

@autotree()
def nodes(self, graph):
    """Return the nodes of a graph.
    TODO: Convert 'nodes' to an instance of something...so you can use it like 'nodes' instead of 'nodes()'
    """
    return graph.nodes()

@autotree("val")
def startswith(self, names):
    "Passed a list, returns all xs where x.startswith(val) is true."
    return [name for name in names if name.startswith(self.val)] 
