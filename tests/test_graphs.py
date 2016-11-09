import unittest
import urllib
from unis.models import *
from unis.runtime import Runtime

from flange.graphs import *
import flange

class Test_graph(unittest.TestCase):
    def test_linear(self):
        g = graph()()
        self.assertEqual(len(g.nodes()), 4)
        self.assertEqual(len(g.edges()), 6)

    def test_ring(self):
        g = graph(topology="ring")()
        self.assertEqual(len(g.nodes()), 4)
        self.assertEqual(len(g.edges()), 4)

    def test_dynamic(self):
        g = graph(topology="dynamic")
        self.assertEqual(len(g().nodes()), 3)
        self.assertEqual(len(g().nodes()), 4)
        self.assertEqual(len(g().nodes()), 5)
        self.assertEqual(len(g().nodes()), 5)
        self.assertEqual(len(g().nodes()), 6)
        self.assertEqual(len(g().nodes()), 3)



class Test_unis(unittest.TestCase):
    explicit_host = "http://192.168.100.200:8888"

    @classmethod
    def _try_connection(cls, url):
        name = cls.__name__
        try: 
            urllib.request.urlopen(url)
        except:
            raise unittest.SkipTest("{0}: Could not connect to UNIS server {1}".format(name, url))

    @classmethod
    def setUpClass(cls):
        unis._runtime_cache = {}

        cls._try_connection(cls.explicit_host)
        cls._try_connection(unis.default_unis)

        try:
            rt = unis()._runtime()
        except Exception as e:
            raise unittest.SkipTest("{0}: Error connecting to UNIS".format(name), e)


        if len(rt.topologies) == 0: 
            raise unittest.SkipTest("{0}: No topologies found in UNIS".format(name))

    def test_implict_host(self):
        b = unis()
        g = b()
        self.assertEqual(len(g.nodes()), 2)
        self.assertEqual(len(g.edges()), 1)

    def test_all_implicit(self):
        b = unis(source=self.explicit_host)
        g = b()
        self.assertEqual(len(g.nodes()), 2)
        self.assertEqual(len(g.edges()), 1)

    def test_all_explicit(self):
        b = unis("*", self.explicit_host)
        g = b()
        self.assertEqual(len(g.nodes()), 2)
        self.assertEqual(len(g.edges()), 1)

    def test_named(self):
        b = unis("test", self.explicit_host)
        g = b()
        self.assertEqual(len(g.nodes()), 2)
        self.assertEqual(len(g.edges()), 1)
