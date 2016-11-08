import unittest
import os
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


class Test_unis(unittest.TestCase):
    explicit_host = "http://192.168.100.200:8888"

    @classmethod
    def setUpClass(cls):
        unis._runtime_cache = {}

        name = cls.__name__
        rsp1 = os.system("ping -c 1 " + cls.explicit_host)
        rsp2 = os.system("ping -c 1 " + unis.default_unis)

        if rsp1 != 0 or rsp !=1:
            raise unittest.SkipTest("{0}: Could not ping UNIS servers".format(name))

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
