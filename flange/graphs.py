from unis.models import *
from unis.runtime import Runtime
import networkx as nx
import itertools
from functools import reduce

from ._internal import FlangeTree, FlangeQuery

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
    linear = {"nodes": ["port1","port2","port3","port4"],
              "edges": [("port1", "port2", True), ("port2", "port3", True),("port3", "port4", True)]}

    ring = {"nodes": ["port1", "port2", "port3", "port4"],
            "edges": [("port1", "port2", False), ("port2", "port3", False),
                      ("port3", "port4", False), ("port4", "port1", False)]}


    dynamic=[{"nodes": ["p1", "p2", "p3"], "edges": []},
             {"nodes": ["p1", "p2", "p3", "p4"], "edges": []},
             {"nodes": ["p1", "p2", "p3", "p4", "p5"], "edges": []},
             {"nodes": ["p1", "p2", "p3", "p4", "p5"], "edges": []},
             {"nodes": ["p1", "p2", "p3", "p4", "p5", "p6"], "edges": []}]

    def __init__(self, topology="linear", nodes=None, edges=None):
        self.dynamic=0

        if nodes or edges:
            self.topology = {"nodes": nodes if nodes else [],
                        "edges": edges if edges else []}
        else:
            try:
                self.topology = graph.__getattribute__(graph, topology)
            except AttributeError as e:
                raise ValueError("No pre-defined graph with name '{0}'".format(topology)) from None


    def __call__(self):
        g = nx.DiGraph()

        try:
            topology = self.topology[self.dynamic]
            self.dynamic = (self.dynamic+1) % len(self.topology)
        except:
            topology = self.topology


        for port in topology["nodes"]:
            g.add_node(port, id=port)

        for (src, sink, symmetric) in topology["edges"]:
            g.add_edge(src, sink)
            if symmetric: g.add_edge(sink, src)

        self.graph = g
        return self.graph


class wrap(FlangeTree):
    "Wrap a reference to a graph"
    def __init__(self, g): self.g = g
    def __call__(self): return self.g


### Graph transformation operators

class select(FlangeQuery):
    def __init__(self, test):
        self.test = test

    def __call__(self, graph):
        return test(graph)

class op(FlangeQuery):
    def __init__(self, fn, *args):
        self.fn = fn
        self.curried = args

    def __call__(self, final):
        args = [x for x in self.curried]
        args.append(final)
        return fn.call(*all_args)

def nodes(graph): return graph.nodes()
def qty(e): return len(e)
def route(path): pass
def chain(*ops): 
    """Apply each operation in a sequence, chaining the result 
    of the first to the input of the second.

    Operations should be f(arg, graph).  Graph is not chained, but remains constant
    through the chaining.
    """

    each_op = lambda op_graph, acc: op_graph[0](acc, op_graph[1])
    return lambda val, graph: reduce(each_op, zip(ops, itertools.repeat(graph)), val)

def startsWith(part): return lambda val, *args: val.startswith(part)
def att(att_id): 
    "Get a node attribute"
    return lambda node_id, graph: nx.get_node_attributes(graph, node_id)[att_id]
