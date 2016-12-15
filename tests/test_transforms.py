import unittest

from flange.transforms import *
from flange.graphs import graph
import flange


class Test_transforms(unittest.TestCase):
    def test_collapse(self):
       g = graph("ring")()
       g2 = contract(nodes)(g)

       self.assertEqual(g2.vertices(), nodes(g).vertices())
       self.assertEqual(len(g2.edges()), 4)

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
