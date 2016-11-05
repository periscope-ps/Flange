from unis.models import *
from unis.runtime import Runtime
import networkx as nx
from ._internal import FlangeTree

class unis(FlangeTree):
    "Retrieves a graph from a UNIS server."
    default_unis = "http://192.168.100.200:8888"
    _runtime_cache = {}

    def __init__(self, ref="*", source=default_unis):
        self.source = source
        self.ref = ref

    def __call__(self):
        rt = self.cached_connection(self.source)

        #TODO: This is a bare-bones buildling of the graph model
        if self.ref == "*": topology = rt
        else: topology= list(rt.topologies.where({"id": self.ref}))[0]

        g = nx.Graph() #TODO: Digraph?
        for port in topology.ports:
            g.add_node(port["id"], **port)
        for link in topology.links:
            g.add_edge(link.endpoints[0], link.endpoints[1], object=link, **link)

        return g

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

    def __init__(self, topology="linear", nodes=None, edges=None):
        g = nx.DiGraph()

        if nodes or edges:
            topology = {"nodes": nodes if nodes else [],
                        "edges": edges if edges else []}
        else:
            try:
                topology = graph.__getattribute__(graph, topology)
            except AttributeError as e:
                raise Exception("No pre-defined graph with name '{0}'".format(topology))


        for port in topology["nodes"]:
            g.add_node(port, id=port)

        for (src, sink, symmetric) in topology["edges"]:
            g.add_edge(src, sink)
            if symmetric: g.add_edge(sink, src)

        self.graph = g

    def __call__(self):
        return self.graph
