import unittest
from flange.locations import *
from flange.graphs import graph
import flange

class Test_inside(unittest.TestCase):
    def test1(self):
        g = graph("ring")
        i = inside(lambda x,g: int(g.node[x]["id"][-1]) < 3)(g())
        r = {(e[0], e[1]) for e in i}
        self.assertEqual(r, {("port1", "port2")})

    def test2(self):
        g = graph("linear",
                  nodes=["port1","port2","port3","port4","port5","port6"], 
                  edges=[("port1", "port2", True), ("port2", "port3", True),("port3", "port4", True),("port4", "port5", True),("port5", "port6", True)])
        i = inside(lambda x,g: int(g.node[x]["id"][-1]) < 5)(g())
        r = {(e[0], e[1]) for e in i}
        self.assertEqual(r, {("port4", "##SINK##")})

    def test3(self):
        g = graph("ring",
                  nodes=["port1","port2","port3","port4","port5"], 
                  edges=[("port1", "port2", True), ("port2", "port3", False),("port3", "port4", False),("port4", "port5", True)])
        i = inside(lambda x,g: int(g.node[x]["id"][-1]) < 5)(g())
        r = {(e[0], e[1]) for e in i}
        self.assertEqual(r, {("port4", "##SINK##")})

class Test_on(unittest.TestCase):
    def test1(self):
        o = on(lambda x,g: int(g.node[x]["id"][-1]) < 3)(graph()())
        self.assertEqual({"port1", "port2"}, set(o.nodes()))
        self.assertEqual(2, len(o.edges()))

    def test2(self):
        g = graph("linear",
                  nodes=["port1","port2","port3","port4","port5"], 
                  edges=[("port1", "port2", True), ("port2", "port3", True),("port3", "port4", False),("port4", "port5", True)])
        o = on(lambda x,g: int(g.node[x]["id"][-1]) < 3)(g())
        self.assertEqual({"port1", "port2"}, set(o.nodes()))
        self.assertEqual(2, len(o.edges()))

    def test3(self):
        g = graph("ring",
                  nodes=["port1","port2","port3","port4","port5"], 
                  edges=[("port1", "port2", True), ("port2", "port3", False),("port3", "port4", False),("port4", "port5", True)])
        o = on(lambda x,g: int(g.node[x]["id"][-1]) < 4)(g())
        self.assertEqual({"port3", "port2", "port1"}, set(o.nodes()))
        self.assertEqual(3, len(o.edges()))

class Test_place(unittest.TestCase):
    def test_placement(self):
        p = flange.place(lambda positions, g: {g.node[n]["id"]: "modified" for n in positions},
                  on(lambda x,g: int(g.node[x]["id"][-1]) < 3))
        self.assertEqual(p(graph()()), {"port1": "modified", "port2": "modified"})

class Test_around(unittest.TestCase):
    def test1(self):
        i = around(lambda x, g: g.node[x]["id"] == "port1")(graph()())
        r = {(e[0], e[1]) for e in i}
        self.assertEqual(r, {("port1", "port2")})

    def test2(self):
        g = graph("linear",
                  nodes=["port1","port2","port3","port4","port5"], 
                  edges=[("port1", "port2", False), ("port2", "port3", False),("port3", "port4", False),("port4", "port5", True)])
        i = around(lambda x, g: g.node[x]["id"] == "port2")(graph()())
        r = {(e[0], e[1]) for e in i}
        self.assertEqual(r, {("port2", "port1"), ("port2", "port3")})

    def test3(self):
        g = graph("ring",
                  nodes=["port1","port2","port3","port4","port5","port6"], 
                  edges=[("port1", "port2", True), ("port2", "port3", False),("port3", "port4", False),("port4", "port5", False),("port5", "port6", True)])
        i = around(lambda x, g: g.node[x]["id"] == "port4")(graph()())
        r = {(e[0], e[1]) for e in i}
        self.assertEqual(r, {("port4", "port3")})

class Test_near(unittest.TestCase):
    def test1(self):
        g = graph()()
        target = g["port2"]
        n = near(lambda x, g: True, lambda x,g: g[x] == target)(g)
        self.assertIn(n, ["port1", "port3"])

    def test2(self):
        g = graph("linear",
                  nodes=["port1","port2","port3","port4","port5","port6"], 
                  edges=[("port1", "port2", False), ("port2", "port3", False),("port3", "port4", False),("port4", "port5", False),("port5", "port6", True)])()
        target = g["port2"]
        n = near(lambda x, g: True, lambda x,g: g[x] == target)(g)
        self.assertIn(n, ["port3"])

    def test3(self):
        g = graph("ring",
                  nodes=["port1","port2","port3","port4","port5","port6"], 
                  edges=[("port1", "port2", True), ("port2", "port3", True),("port3", "port4", True),("port4", "port5", False),("port5", "port6", True)])()
        target = g["port6"]
        n = near(lambda x, g: True, lambda x,g: g[x] == target)(g)
        self.assertIn(n, ["port5"])

