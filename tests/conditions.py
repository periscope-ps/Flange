import unittest
import flange
from flange.graphs import graph
from flange.conditions import *

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
