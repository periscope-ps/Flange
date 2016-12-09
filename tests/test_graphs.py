import unittest
import urllib
from unis.models import *
from unis.runtime import Runtime

from flange.graphs import *
import flange

class Test_transforms(unittest.TestCase):
    def test_nodes(self):
        g = graph("ring")()
        g2 = nodes(g)
        self.assertEqual(len(g2.vertices()), len(graph.ring["vertices"]))
    

    def test_all_att(self):
        g = graph("ring")
        t = nodes >> all_att("id", lambda id: int(id[-1]) < 3)
        g2 = t(g())
        self.assertEqual({'port1', 'port2'}, set(g2.vertices()))


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

#class Test_unis(unittest.TestCase):
#    explicit_host = "http://192.168.100.200:8888"
#
#    @classmethod
#    def _try_connection(cls, url):
#        name = cls.__name__
#        try: 
#            urllib.request.urlopen(url)
#        except:
#            raise unittest.SkipTest("{0}: Could not connect to UNIS server {1}".format(name, url))
#
#    @classmethod
#    def setUpClass(cls):
#        unis._runtime_cache = {}
#
#        cls._try_connection(cls.explicit_host)
#        cls._try_connection(unis.default_unis)
#
#        try:
#            rt = unis()._runtime()
#        except Exception as e:
#            raise unittest.SkipTest("{0}: Error connecting to UNIS".format(name), e)
#
#
#        if len(rt.topologies) == 0: 
#            raise unittest.SkipTest("{0}: No topologies found in UNIS".format(name))
#
#    def test_implict_host(self):
#        b = unis()
#        g = b()
#        self.assertEqual(len(g.vertices()), 2)
#        self.assertEqual(len(g.edges()), 1)
#
#    def test_all_implicit(self):
#        b = unis(source=self.explicit_host)
#        g = b()
#        self.assertEqual(len(g.vertices()), 2)
#        self.assertEqual(len(g.edges()), 1)
#
#    def test_all_explicit(self):
#        b = unis("*", self.explicit_host)
#        g = b()
#        self.assertEqual(len(g.vertices()), 2)
#        self.assertEqual(len(g.edges()), 1)
#
#    def test_named(self):
#        b = unis("test", self.explicit_host)
#        g = b()
#        self.assertEqual(len(g.vertices()), 2)
#        self.assertEqual(len(g.edges()), 1)
