import unittest
from unis.models import *
from unis.runtime import Runtime
from flange.conditions import *
from flange.roots import *
from flange.graphs import *
from flange.locations import *
import flange

def test(case=None):
    "Run tests by name...helpful in jupyter notebook"
    import sys

    unis._runtime_cache = {}
    print("Cleared unis Runtime cache")

    if case is None:
        module = sys.modules[__name__]
        suite = unittest.TestLoader().loadTestsFromModule(module)
    else:
        suite = unittest.TestLoader().loadTestsFromTestCase(case)
    unittest.TextTestRunner().run(suite)

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


class Test_rule(unittest.TestCase):
    def test_action_pass(self):
        c = rule(lambda x: 4<x[0], lambda x: [[6]])
        self.assertEqual(c([3]), [[6]])

    def test_simple_pass(self):
        c = rule(lambda x: 4>3, lambda x: [[3]])
        self.assertEqual(c(5), (5,))

    def test_double_fail(self):
        c = rule(lambda *x: 4<3, lambda *x: [4])
        self.assertRaises(flange.ActionFailureError, c)

class Test_switch(unittest.TestCase):
    FALSE = lambda *x: False
    TRUE = lambda *x: True

    def test_last(self):
        s = switch(rule(self.FALSE, lambda *x: None),
                   rule(self.FALSE, lambda *x: None),
                   rule(self.FALSE, lambda *x: None),
                   switch.default(lambda *x: 10))
        self.assertEqual(s(), 10)

    def test_intermediate(self):
        s = switch(rule(self.FALSE, lambda *x: None),
                   rule(self.TRUE, lambda *x: 6),
                   rule(self.FALSE, lambda *x: None),
                   switch.default(lambda *x: 10))
        self.assertEqual(s(), 6)

    def test_default_rule(self):
        r = switch.default(lambda *x: 3)
        self.assertEqual(r.test(), True)

    def test_no_valid(self):
        s = switch(rule(self.FALSE, lambda *x: None),
                   rule(self.FALSE, lambda *x: None),
                   rule(self.FALSE, lambda *x: None))
        self.assertRaises(flange.NoValidChoice, s)

class Test_unis(unittest.TestCase):
    explicit_host = "http://192.168.100.200:8888"

    @classmethod
    def setUpClass(cls):
        unis._runtime_cache = {}

        name = cls.__name__
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


class Test_graph(unittest.TestCase):
    def test_linear(self):
        g = graph()()
        self.assertEqual(len(g.nodes()), 4)
        self.assertEqual(len(g.edges()), 6)

    def test_ring(self):
        g = graph(topology="ring")()
        self.assertEqual(len(g.nodes()), 4)
        self.assertEqual(len(g.edges()), 4)

class TestGroupConditions(unittest.TestCase):
    def test_exists_pass(self):
        t = exists(lambda n, g: g.degree(n) > 0,
                   lambda g: g.nodes(),
                   graph())
        self.assertTrue(t())

    def test_exists_fail(self):
        t = exists(lambda n, g: g.degree(n) == 0,
                   lambda g: g.nodes(),
                   graph())
        self.assertFalse(t())

    def test_exactlyone_pass(self):
        t = exists(lambda n, g: g.node[n]["id"] == "port1",
                   lambda g: g.nodes(),
                   graph())
        self.assertTrue(t())

    def test_exactlyOne_fail(self):
        t = exactlyOne(lambda n, g: g.degree(n) == 0,
                   lambda g: g.nodes(),
                   graph())
        self.assertFalse(t())

        t = exactlyOne(lambda n, g: g.degree(n) > 0,
                   lambda g: g.nodes(),
                   graph())
        self.assertFalse(t())

    def test_all_pass(self):
        t = all(lambda n, g: g.degree(n) > 0,
                   lambda g: g.nodes(),
                   graph())
        self.assertTrue(t())

    def test_all_fail(self):
        t = all(lambda n, g: g.node[n]["id"] == "port1",
                   lambda g: g.nodes(),
                   graph())
        self.assertFalse(t())

    def test_most_pass(self):
        t = most(lambda n, g: int(g.node[n]["id"][-1]) < 3,
                 lambda g: g.nodes(),
                 graph())
        self.assertTrue(t())

    def test_most_fail(self):
        t = most(lambda n, g: g.node[n]["id"] == "port3",
                 lambda g: g.nodes(),
                 graph())
        self.assertFalse(t())


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
