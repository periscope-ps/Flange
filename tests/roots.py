import unittest

from flange.conditions import *
from flange.roots import *
from flange.graphs import *
import flange

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
