import unittest
import networkx as nx
from flange.utils import *
from flange.graphs import *
import flange

class Test_diff(unittest.TestCase):
    def test_del_prop(self):
        changed = "port1"
        attribute = "att2"

        g1 = graph("linear")()
        nx.set_vertex_attributes(g1, "att", 0)
        nx.set_vertex_attributes(g1, attribute, 13)
        g2 = g1.copy()

        del g2.vertex[changed][attribute]

        delta = diff(g1,g2)
        self.assertEqual(1, len(delta))
        self.assertEqual(changed, list(delta.keys())[0])
        self.assertTrue("props" in delta[changed].keys())
        self.assertEqual("prop removed", delta[changed]["props"][attribute])


    def test_new_prop(self):
        attribute = "att2"
        val = 34
        g1 = graph("linear")()
        nx.set_vertex_attributes(g1, "att", 0)
        g2 = g1.copy()
        nx.set_vertex_attributes(g2, attribute, val)

        delta = diff(g1,g2)
        changed = list(delta.keys())[0]
        self.assertEqual(len(g1), len(delta))
        self.assertTrue("props" in delta[changed].keys())
        self.assertEqual("prop added", delta[changed]["props"][attribute])

    def test_changed_prop(self):
        g1 = graph("linear")()
        nx.set_vertex_attributes(g1, "att", 0)
        g2 = g1.copy()

        changed = "port3"
        attribute = "att"
        new_val = 34

        g2.vertex[changed][attribute] = new_val

        delta = diff(g1,g2)
        self.assertEqual(1, len(delta))
        self.assertEqual(changed, list(delta.keys())[0])
        self.assertTrue("props" in delta[changed].keys())
        self.assertEqual(new_val, delta[changed]["props"][attribute])


    def test_del_node(self):
        g1 = graph("linear")()
        verts = g1.vertices()
        remove = verts[0]
        g2 = g1.subgraph(verts[1:])

        delta = diff(g1,g2)
        self.assertEqual(len(delta), 1)
        self.assertEqual(list(delta.keys())[0], remove)
        self.assertTrue(delta[remove]["deleted"])

    def test_new_node(self):
        g1 = graph("linear")()
        g2 = g1.copy()
        new = "newly_added"
        g2.add_vertex(new)

        delta = diff(g1,g2)
        self.assertEqual(len(delta), 1)
        self.assertEqual(list(delta.keys())[0], new)
        self.assertTrue(delta[new]["added"])
