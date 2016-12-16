import unittest

from flange._internal import *

class ONE(FlangeTree):
    def __call__(self, ls): 
        ls.append(1)
        return ls

class TWO(FlangeTree):
    def __call__(self, ls):
        ls.append(2)
        return ls

class Test_chain(unittest.TestCase):
    def test_left(self):
        fn = ONE() << TWO()
        rs = fn([])
        self.assertEqual([2,1], rs)

    def test_right(self):
        fn = ONE() >> TWO()
        rs = fn([])
        self.assertEqual([1,2], rs)
