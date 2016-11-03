from unis.models import *
from unis.runtime import Runtime
import networkx as nx

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
              "edges": [("port1", "port2"), ("port2", "port3"),("port3", "port4")]}

    def __init__(self, topology="linear", nodes=None, edges=None):
        g = nx.Graph()

        if nodes or edges:
            topology = {"nodes": nodes if nodes else [],
                        "edges": edges if edges else []}
        else:
            topology = graph.__getattribute__(graph, topology)


        for port in topology["nodes"]:
            g.add_node(port, id=port)

        for link in topology["edges"]:
            g.add_edge(link[0], link[1])

        self.graph = g

    def __call__(self):
        return self.graph
