import unittest

import flange
from flange.graphs import graph
from flange.transforms import nodes
from flange.conditions import *

class TestGroupConditions(unittest.TestCase):
    def test_exists_pass(self):
        t = exists(lambda n, g: g.degree(n) > 0,
                   lambda g: g.vertices())
        self.assertTrue(t(graph("linear")()))

    def test_exists_fail(self):
        t = exists(lambda n, g: g.degree(n) == 0,
                   lambda g: g.vertices())
        self.assertFalse(t(graph("linear")()))

    def test_exactlyone_pass(self):
        t = exists(lambda n, g: g.vertex[n]["id"] == "port1",
                   lambda g: g.vertices())
        self.assertTrue(t(graph("linear")()))

    def test_exactlyOne_fail(self):
        t = exactlyOne(lambda n, g: g.degree(n) == 0,
                   lambda g: g.vertices())
        self.assertFalse(t(graph("linear")()))

        t = exactlyOne(lambda n, g: g.degree(n) > 0,
                   lambda g: g.vertices())
        self.assertFalse(t(graph("linear")()))

    def test_all_pass(self):
        t = all(lambda n, g: g.degree(n) > 0,
                   lambda g: g.vertices())
        self.assertTrue(t(graph("linear")()))

    def test_all_fail(self):
        t = all(lambda n, g: g.vertex[n]["id"] == "port1",
                   lambda g: g.vertices())
        self.assertFalse(t(graph("linear")()))

    def test_most_pass(self):
        t = most(lambda n, g: int(g.vertex[n]["id"][-1]) < 3,
                 nodes)
        self.assertTrue(t(graph("linear")()))

    def test_most_fail(self):
        t = most(lambda n, g: g.vertex[n]["id"] == "port3",
                 lambda g: g.vertices())
        self.assertFalse(t(graph("linear")()))
