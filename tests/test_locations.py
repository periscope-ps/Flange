import unittest
from flange.locations import *
from flange.graphs import graph
import flange

class Test_inside(unittest.TestCase):
    def test(self):
        g = graph("ring")
        i = inside(lambda x,g: int(g.node[x]["id"][-1]) < 3)(g())
        r = {(e[0], e[1]) for e in i}
        self.assertEqual(r, {("port1", "port2")})

class Test_on(unittest.TestCase):
    def test(self):
        o = on(lambda x,g: int(g.node[x]["id"][-1]) < 3)(graph()())
        self.assertEqual({"port1", "port2"}, set(o.nodes()))
        self.assertEqual(2, len(o.edges()))

class Test_place(unittest.TestCase):
    def test_placement(self):
        p = flange.place(lambda positions, g: {g.node[n]["id"]: "modified" for n in positions},
                  on(lambda x,g: int(g.node[x]["id"][-1]) < 3),
                  graph())
        self.assertEqual(p(), {"port1": "modified", "port2": "modified"})

class Test_around(unittest.TestCase):
    def test(self):
        i = around(lambda x, g: g.node[x]["id"] == "port1")(graph()())
        r = {(e[0], e[1]) for e in i}
        self.assertEqual(r, {("port1", "port2")})

class Test_near(unittest.TestCase):
    def test(self):
        g = graph()()
        target = g["port2"]
        n = near(lambda x, g: True, lambda x,g: g[x] == target)(g)
        self.assertIn(n, ["port1", "port3"])
