import unittest
import random

from flange.conditions import *
from flange.roots import *
from flange.graphs import *
import flange

class Test_rule(unittest.TestCase):
    def test_action_pass(self):
        c = rule(lambda x: 4<x[0], lambda x: [6])
        self.assertEqual(c([3]), [6])

    def test_simple_pass(self):
        c = rule(lambda x: 4>3, lambda x: [[3]])
        self.assertEqual(c(5), 5)

    def test_double_fail(self):
        c = rule(lambda *x: 4<3, lambda *x: [4])
        self.assertRaises(flange.ActionFailureError, c, None)

class Test_switch(unittest.TestCase):
    FALSE = lambda *x: False
    TRUE = lambda *x: True

    def test_last(self):
        s = switch(rule(self.FALSE, lambda *x: None),
                   rule(self.FALSE, lambda *x: None),
                   rule(self.FALSE, lambda *x: None),
                   switch.default(lambda *x: 10))
        self.assertEqual(s(None), 10)

    def test_intermediate(self):
        s = switch(rule(self.FALSE, lambda *x: None),
                   rule(self.TRUE, lambda *x: 6),
                   rule(self.FALSE, lambda *x: None),
                   switch.default(lambda *x: 10))
        self.assertEqual(s(None), 6)

    def test_default_rule(self):
        r = switch.default(lambda *x: 3)
        self.assertEqual(r.test(), True)

    def test_no_valid(self):
        s = switch(rule(self.FALSE, lambda *x: None),
                   rule(self.FALSE, lambda *x: None),
                   rule(self.FALSE, lambda *x: None))
        self.assertRaises(flange.NoValidChoice, s, None)


class Test_monitor(unittest.TestCase):
    def test_always_run(self):
        base = range(100).__iter__()
        root = lambda g: 1 
        gate = lambda g: next(base) 
        self.execute(root, gate, 10, 0)

    def test_node_gate(self):
        root = lambda g: 1
        gate = lambda g: len(g.vertices())
        self.execute(root, gate, 4, 1)

    def execute(self, root, gate, expected_execs, expected_skips):
        g = graph("dynamic")
        m = monitor(root, gate)

        execs = 0
        skips = 0
        for i in range(expected_execs+expected_skips):
            try:
                m(g())
                execs = execs + 1
            except NoChange:
                skips = skips + 1

        self.assertEqual(execs, expected_execs)
        self.assertEqual(skips, expected_skips)


class Test_assert(unittest.TestCase):
    def test(self):
        pass

