import unittest
from flange.actions import *
from flange.graphs import *
import flange

class Test_place(unittest.TestCase):
    def test_placement(self):
        g = graph("linear")
        action = set_att("firewall", True)
        location = flange.between(sub("port2"), sub("port4")) >> nodes

        p = place(action, location)
        g2 = p(g())
        self.assertTrue(g2.vertex["port3"]["firewall"])
