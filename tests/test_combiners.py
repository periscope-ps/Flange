import unittest
from flange.graphs import *
import flange
import flange.combiners as combiners

class Test_combiners(unittest.TestCase):

    def test_fair_merge(self):
        self.assertRaises(Exception, combiners.fair_merge()) 
