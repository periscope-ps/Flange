import unittest
from flange.locations import *
from flange.graphs import * 

class Test_across(unittest.TestCase):
    def test(self):
        g = graph("ring")()
        src = all_att("id", "port1")
        dst = all_att("id", "port3")
        g2 = across(src,dst)(g)

        partitioned = [v for v in g.vertices() if v not in g2.vertices()]
        self.assertFalse(nx.is_strongly_connected(g.subgraph(partitioned)))

class Test_on(unittest.TestCase):
    def test(self):
        selector =  nodes >> all_att("id", lambda id: int(id[-1]) < 3)
        g = graph("linear")
        g2 = on(selector)(g())
        self.assertEqual({"port1", "port2"}, set(g2.vertices()))

class Test_around(unittest.TestCase):
    def test(self):
        g = graph("linear")
        s = lambda g: g.subgraph("port1")
        i = around(s)(g())
        self.assertEqual(set(i.vertices()), {('port2', 'port1'), ('port1', 'port2')})

class Test_near(unittest.TestCase):
    def test_middle(self):
        g = graph("linear")()
        target = g["port2"]
        n = near(nodes, lambda x,g: g[x] == target)(g)
        self.assertEqual(len(n.vertices()), 1)
        self.assertIn(n.vertices()[0], ["port1", "port3"])

    def test_spur(self):
        g = graph("linear")()
        target = g["port4"]
        n = near(nodes, lambda x,g: g[x] == target)(g)
        self.assertEqual(len(n.vertices()), 1)
        self.assertEqual(n.vertices()[0], "port3")


class Test_bewteen(unittest.TestCase):
    def test(self):
        g = graph("linear")
        g2 = between(sub("port2"), sub("port4"))(g())

        self.assertEqual(3, len(g2.vertices()))
        self.assertEqual("port3", nodes(g2).vertices()[0])
