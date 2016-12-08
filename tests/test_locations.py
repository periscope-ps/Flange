import unittest
from flange.locations import *
from flange.graphs import graph, nodes
import flange

class Test_across(unittest.TestCase):
    def test(self):
        g = graph("ring")
        i = across(lambda x,g: int(g.vertex[x]["id"][-1]) < 3)(g())
        r = {(e[0], e[1]) for e in i}
        self.assertEqual(r, {("port1", "port2")})

class Test_on(unittest.TestCase):
    def test(self):
        o = on(lambda x,g: int(g.vertex[x]["id"][-1]) < 3)(graph()())
        self.assertEqual({"port1", "port2"}, set(o.vertices()))
        self.assertEqual(2, len(o.edges()))

class Test_place(unittest.TestCase):
    def test_placement(self):
        p = flange.place(lambda positions, g: {g.vertex[n]["id"]: "modified" for n in positions},
                  on(lambda x,g: int(g.vertex[x]["id"][-1]) < 3))
        self.assertEqual(p(graph()()), {"port1": "modified", "port2": "modified"})

class Test_around(unittest.TestCase):
    def test(self):
        i = around(lambda x, g: g.vertex[x]["id"] == "port1")(graph()())
        r = {(e[0], e[1]) for e in i}
        self.assertEqual(r, {("port1", "port2")})

class Test_near(unittest.TestCase):
    def test(self):
        g = graph()()
        target = g["port2"]
        n = near(nodes, lambda x,g: g[x] == target)(g)
        self.assertEquals(len(n.vertices()), 1)
        self.assertIn(n.vertices()[0], ["port1", "port3"])


        g = graph()()
        target = g["port4"]
        n = near(nodes, lambda x,g: g[x] == target)(g)
        self.assertEquals(len(n.vertices()), 1)
        self.assertEquals(n.vertices()[0], "port3")
