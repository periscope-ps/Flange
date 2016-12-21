import networkx as nx
from itertools import chain

from ._internal import FlangeTree


class graph(FlangeTree):
    linear = {"nodes": ["port1","port2","port3","port4"],
              "links": [("port1", "port2"), ("port2", "port3"),("port3", "port4"),
                        ("port2", "port1"), ("port3", "port2"),("port4", "port3")]}

    ring = {"nodes": ["port1", "port2", "port3", "port4"],
            "links": [("port1", "port2"), ("port2", "port3"),
                      ("port3", "port4"), ("port4", "port1")]}

    dynamic=[{"nodes": ["p1", "p2", "p3"], "links": []},
             {"nodes": ["p1", "p2", "p3", "p4"], "links": []},
             {"nodes": ["p1", "p2", "p3", "p4", "p5"], "links": []},
             {"nodes": ["p1", "p2", "p3", "p4", "p5"], "links": []},
             {"nodes": ["p1", "p2", "p3", "p4", "p5", "p6"], "links": []}]

    ab_ring = {"nodes": ["A1", "A2", "A3", "A4", "A5", "B1", "B2", "B3"],
               "links": [("A1", "A2"), ("A2", "A3"), ("A3", "B1"), 
                        ("B1", "A4"), 
                        ("A4", "B2"), ("B2", "B3"), ("B3", "A5"),
                        ("A5", "A1")]}

    layers = {"nodes": ["Z1", "A1", "A2", "A3", "B1", "B2", "C1", "C2", "D1"],
              "links": [("Z1", "A1"), ("Z1", "A2"), ("Z1", "A3"),
                        ("A1", "Z1"), ("A2", "Z1"), ("A3", "Z1"),
                        ("A1", "B1"), ("A1", "B2"), ("A2", "B1"), ("A2", "B2"), ("A3", "B1"), ("A3", "B2"),
                        ("B1", "A1"), ("B2", "A1"), ("B1", "A2"), ("B2", "A2"), ("B1", "A3"), ("B2", "A3"),
                        ("B1", "C1"), ("B2", "C1"), ("B1", "C2"), ("B2", "C2"),
                        ("C1", "B1"), ("C1", "B2"), ("C2", "B1"), ("C2", "B2"),
                        ("C1", "D1"), ("C2", "D1"),
                        ("D1", "C1"), ("D1", "C2")]}


    osiris = {"nodes":["IU", "WSU", "MSU", "CHIC", "SALT", "SC16", "IU-Crest", "UMich", "Cloudlab"],
              "links": [("IU", "CHIC"), ("CHIC", "IU"),
                        ("UMich", "CHIC"), ("CHIC", "UMich"),
                        ("WSU", "CHIC"), ("CHIC", "WSU"),
                        ("MSU", "CHIC"), ("CHIC", "MSU"),
                        ("SALT","CHIC"), ("CHIC", "SALT"),
                        ("Cloudlab", "SALT"), ("SALT", "Cloudlab"), 
                        ("SC16", "SALT"), ("SALT", "SC16"), 
                        ("SC16", "UMich"), ("UMich", "SC16"),
                        ("SC16", "IU-Crest"), ("IU-Crest", "SC16")]}

    def __init__(self, topology=None, *, nodes=None, links=None):
        self.dynamic=0

        if topology is not None \
           and (nodes is not None
                or links is not None):
            raise ValueError("Specify topology OR nodes & links.  Not both.")

        if nodes is not None\
           or links is not None:
            self.topology = {"nodes": nodes if nodes else [],
                             "links": links if links else []}
        else:
            try:
                self.topology = graph.__getattribute__(graph, topology)
            except (AttributeError, TypeError) as e:
                raise ValueError("No pre-defined graph with name '{0}'".format(topology)) from None


    def __call__(self):
        try:
            topology = self.topology[self.dynamic]
            self.dynamic = (self.dynamic+1) % len(self.topology)
        except:
            topology = self.topology

        vertices = [(name, {"id": name, "_type": "node"}) 
                    for name in topology["nodes"]]
        vertices.extend([(vertex, {"id": vertex, "_type": "link"}) 
                         for vertex in topology["links"]])
        edges = [((src, (src,dst)), ((src,dst), dst)) 
                 for (src, dst) in topology["links"]]

        g = nx.DiGraph()

        g.add_vertices_from(vertices)
        g.add_edges_from(chain(*edges))
        self.graph = g
        return self.graph


class wrap(FlangeTree):
    "Wrap a reference to a graph"
    def __init__(self, g): self.g = g
    def __call__(self): return self.g


import importlib
unis_found = importlib.util.find_spec("unis") is not None

if unis_found:
    from unis.models import *
    from unis.runtime import Runtime
    class unis(FlangeTree):
        "Retrieves a graph from a UNIS server."
        default_unis = "http://192.168.100.200:8888"
        _runtime_cache = {}

        def __init__(self, topology="*", *, host=default_unis):
            self.source = source
            self.topology = topology

        def __call__(self):
            #TODO: This is a bare-bones buildling of the graph model; make it better
            rt = self._runtime()
            topology = rt

            if not self.topology == "*": 
                try:
                    topology= list(rt.topologies.where({"id": self.topology}))[0]
                except IndexError:
                    raise ValueError("No topology named '{0}' found in UNIS instance {1}".format(self.topology, self.source)) from None 
                
            g = nx.DiGraph() 
            for port in topology.ports:
                #HACK: Grabbing __dict__ probably won't work for long...
                g.add_vertex(port.id, **port.__dict__)

            # Assumes endpoints exist in vertex list, just adds the edge-vertex
            for link in topology.links:
                g.add_vertex(link.id, **link.__dict__)

                if not link.directed:
                    g.add_edge(link.endpoints[0].id, link.id)
                    g.add_edge(link.id, link.endpoints[0].id)
                    
                    g.add_edge(link.endpoints[1].id, link.id)
                    g.add_edge(link.id, link.endpoints[1].id)

                else:
                    g.add_edge(link.source.id, link.id)
                    g.add_edge(link.id, link.sink.id)


            return g

        def _runtime(self):
            return self.cached_connection(self.source)

        @classmethod
        def cached_connection(cls, source):
            rt = cls._runtime_cache.get(source, Runtime(source))
            cls._runtime_cache[source] = rt
            return rt


