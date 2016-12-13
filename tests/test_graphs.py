import unittest
import urllib
from unis.models import *
from unis.runtime import Runtime

from flange.graphs import *
import flange

class Test_transforms(unittest.TestCase):
    def test_vertices(self):
        g = graph("ring")()
        g2 = nodes(g)
        self.assertEqual(len(g2.vertices()), len(graph.ring["vertices"]))

    def test_set_att(self):
        g = graph("linear")()
        t = set_att("firewall", True)

        #Not in-place test
        for v in g.vertices():
            self.assertFalse(g.vertex[v].get("firewall", False))
        g2 = t(g)
        self.assertIsNot(g, g2)
        for v in g.vertices():
            self.assertTrue(g2.vertex[v].get("firewall", False))

        #In-place test 
        for v in g.vertices():
            self.assertFalse(g.vertex[v].get("firewall", False))
        g2 = t(g, inplace=True)

        self.assertIs(g, g2)
        for v in g.vertices():
            self.assertTrue(g2.vertex[v].get("firewall", False))

    def test_subgraph(self):
        g = graph("layers")()
        t = sub("A1")
        self.assertEqual(1, len(t(g)))

        t = sub(lambda x: int(x[-1]) == 1)
        self.assertEqual(5, len(t(nodes(g))))

    def test_all_att(self):
        g = graph("ring")
        t = nodes >> all_att("id", lambda id: int(id[-1]) < 3)
        g2 = t(g())
        self.assertEqual({'port1', 'port2'}, set(g2.vertices()))


    def test_neighbors(self):
        g = graph("layers")
        selector = nodes >> all_att("id", lambda id: int(id[-1]) == 1)
        transform = neighbors(selector)
        g2 = transform(g())
        self.assertEqual(29, len(g2.vertices()))
        self.assertIn("A1", g2.vertices())
        self.assertIn("B1", g2.vertices())
        self.assertIn("C1", g2.vertices())
        self.assertIn("Z1", g2.vertices())
        self.assertTrue(nx.is_weakly_connected(g2)) #Not true for all neighbors graphs, but is true for the layers one

        transform = neighbors(selector, external=False)
        g2 = transform(g())
        self.assertEqual(13, len(g2.vertices()))


class Test_graph(unittest.TestCase):
    def test_linear(self):
        g = graph("linear")()
        self.assertEqual(len(g.vertices()), 10)
        self.assertEqual(len(g.edges()), 12)

    def test_ring(self):
        g = graph(topology="ring")()
        self.assertEqual(len(g.vertices()), 8)
        self.assertEqual(len(g.edges()), 8)

    def test_dynamic(self):
        g = graph(topology="dynamic")
        self.assertEqual(len(g().vertices()), 3)
        self.assertEqual(len(g().vertices()), 4)
        self.assertEqual(len(g().vertices()), 5)
        self.assertEqual(len(g().vertices()), 5)
        self.assertEqual(len(g().vertices()), 6)
        self.assertEqual(len(g().vertices()), 3)

    def test_manual(self):
        g = graph(vertices=["port1","port2","port3","port4","port5","port6"], 
                  edges=[("port1", "port2"), ("port2", "port1"),
                         ("port2", "port3"), ("port3", "port2"),
                         ("port3", "port4"), ("port4", "port3"),
                         ("port4", "port5"), ("port5", "port4"),
                         ("port5", "port6"), ("port6", "port5")])()
        self.assertEqual(len(g.vertices()), 16)
        self.assertEqual(len(g.edges()), 20)


class Test_unis(unittest.TestCase):
    explicit_host = "http://192.168.100.200:8888"

    @classmethod
    def _try_connection(cls, url):
        name = cls.__name__
        try: 
            urllib.request.urlopen(url, timeout=2)
        except:
            raise unittest.SkipTest("{0}: Timeout connecting to UNIS server {1}".format(name, url))

    @classmethod
    def setUpClass(cls):
        unis._runtime_cache = {}

        cls._try_connection(cls.explicit_host)
        cls._try_connection(unis.default_unis)

        try:
            rt = unis()._runtime()
        except Exception as e:
            raise unittest.SkipTest("{0}: Error connecting to UNIS".format(name), e)

        populate()
        if len(rt.topologies) == 0: 
            raise unittest.SkipTest("{0}: No topologies found in UNIS".format(name))


    def test_implict_host(self):
        b = unis()
        g = b()
        self.assertEqual(len(g.vertices()), 2)
        self.assertEqual(len(g.edges()), 1)

    def test_all_implicit(self):
        b = unis(source=self.explicit_host)
        g = b()
        self.assertEqual(len(g.vertices()), 2)
        self.assertEqual(len(g.edges()), 1)

    def test_all_explicit(self):
        b = unis("*", self.explicit_host)
        g = b()
        self.assertEqual(len(g.vertices()), 2)
        self.assertEqual(len(g.edges()), 1)

    def test_named(self):
        b = unis("test", self.explicit_host)
        g = b()
        self.assertEqual(len(g.vertices()), 2)
        self.assertEqual(len(g.edges()), 1)


def populate(url):
    "Place test topology into UNIS"
    with Runtime(url) as rt:
        node1 = Node({"id": "node1"})
        node2 = Node({"id": "node2"})
        node3 = Node({"id": "node3"})
        node4 = Node({"id": "node4"})
        port1 = Port({"id": "port1"})
        port2 = Port({"id": "port2"})
        port3 = Port({"id": "port3"})
        port4 = Port({"id": "port4"})

        node1.ports.append(port1)
        node2.ports.append(port2)
        node2.ports.append(port3)
        node2.ports.append(port4)
        link1 = Link({"id": "link1-2", "directed": False, "endpoints": [port1, port2]})
        link2 = Link({"id": "link2-3", "directed": False, "endpoints": [port2, port3]})
        link3 = Link({"id": "link3-4", "directed": False, "endpoints": [port3, port4]})
        topology = Topology({"id": "test",
                             "ports" : [port1, port2, port3, port4],
                             "nodes": [node1, node2, node3, node4],
                             "links" : [link1, link2, link3]})

        rt.insert(port1, commit=True)
        rt.insert(port2, commit=True)
        rt.insert(port3, commit=True)
        rt.insert(port4, commit=True)
        rt.insert(node1, commit=True)
        rt.insert(node2, commit=True)
        rt.insert(node3, commit=True)
        rt.insert(node4, commit=True)
        rt.insert(link1, commit=True)
        rt.insert(link2, commit=True)
        rt.insert(link3, commit=True)
        rt.insert(topology, commit=True)


