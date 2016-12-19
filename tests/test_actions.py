import unittest
import networkx as nx
from flange.actions import *
from flange.graphs import graph
from flange.transforms import set_att, sub, nodes
import flange

class Test_place(unittest.TestCase):
    def test_placement(self):
        g = graph("linear")
        action = set_att("firewall", True)
        location = flange.between(sub("port2"), sub("port4")) >> nodes

        p = place(action, location)
        g2 = p(g())
        self.assertTrue(g2.vertex["port3"]["firewall"])

class Test_update(unittest.TestCase):
    def test_add_property(self):
        g1 = graph("linear")()
        u = nx.DiGraph()
        u.add_vertex("port1")
        nx.set_vertex_attributes(u, "firewall", True)


        g2 = update(g1, u)
        self.assertTrue(g2.vertex["port1"]["firewall"])
        self.assertEqual(set(g1.vertices()), set(g2.vertices()))
