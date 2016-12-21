import unittest

from flange.graphs import *
from flange.fairflow import *
import flange
import flange.combiners as combiners
import networkx as nx

class Test_combiners(unittest.TestCase):
    
    def test_fair_merge(self):
        self.assertRaises(Exception, combiners.fair_merge()) 

    def test_priority(self):
        def raiseEx(exc):
            raise Exception (exc)
        
        graph = build_graph()
        alloc_man1 = Alloc_Manager()
        alloc_man2 = Alloc_Manager()
        alloc_man3 = Alloc_Manager()
        alloc_man4 = Alloc_Manager()

        self.assertRaises(Exception,
                          combiners.priority("B4_Max_Min", 
                                             (lambda g: alloc_man1(g, [app("app1", 10, 'A', 'B', 15), app("app2", 1, 'A', 'B', 5), app("app3", 0.5, 'A', 'C', 10)], B4_Max_Min_Fairshare())),
                                             (lambda g: alloc_man2(g, [app("app4", 8, 'C', 'D', 5), app("app5", 1, 'A', 'F', 5), app("app6", 2.5, 'B', 'C', 10)], B4_Max_Min_Fairshare())),
                                             (lambda g: alloc_man3(g, [app("app7", 1, 'D', 'E', 2), app("app8", 1, 'E', 'F', 5)], B4_Max_Min_Fairshare())),
                                             (lambda g: raiseEx ("A<->B Link Out of Capacity") if g.edge['A']['B']['weight'] == 0 else g),
                                             (lambda g: alloc_man4(g.graph, [app("app9", 1, 'B', 'D', 4)], B4_Max_Min_Fairshare()))),
                          graph)

        self.assertEqual(round((alloc_man1.get_flowgroup_by_id("FLWG-AB")).allocated), 20)
        self.assertEqual(round((alloc_man1.get_flowgroup_by_id("FLWG-AC")).allocated), 8)
        self.assertEqual(round((alloc_man2.get_flowgroup_by_id("FLWG-CD")).allocated, 2), 1.75)
        self.assertEqual(round((alloc_man2.get_flowgroup_by_id("FLWG-AF")).allocated, 2), 2)
        self.assertEqual(round((alloc_man2.get_flowgroup_by_id("FLWG-BC")).allocated, 2), 0.25)
        self.assertEqual(round((alloc_man3.get_flowgroup_by_id("FLWG-DE")).allocated), 0)
        self.assertEqual(round((alloc_man3.get_flowgroup_by_id("FLWG-EF")).allocated), 3)
        #self.assertEqual(round((alloc_man4.get_flowgroup_by_id("FLWG-BD")).allocated), 4)

    def test_best(self):
        graph = build_graph()
        graph.remove_node('E')
        alloc_man1 = Alloc_Manager()
        alloc_man2 = Alloc_Manager()

        def bandwidth_alloc(g, alloc_man, algorithm):
            g = alloc_man(g, [app("app1", 10, 'B', 'F', 25), app("app2", 1, 'D', 'F', 2)], algorithm)
            return alloc_man

        def weight_func(alloc_man):
            return (alloc_man.get_flowgroup_by_id("FLWG-DF").allocated * 10) 
        
        alloc_man = combiners.best((lambda alloc_man: weight_func(alloc_man)),
                                   "Bandwidth_Allocation",
                                   (lambda g: bandwidth_alloc(g, alloc_man1, Bandwidth_Inorder())),
                                   (lambda g: bandwidth_alloc(g, alloc_man2, B4_Max_Min_Fairshare())))(graph)

        self.assertEqual(alloc_man.get_flowgroup_by_id("FLWG-DF").allocated, 2)

    def test_best_effort(self):
        def raiseEx(exc):
            raise Exception (exc)
        
        graph = build_graph()
        alloc_man1 = Alloc_Manager()
        alloc_man2 = Alloc_Manager()
        alloc_man3 = Alloc_Manager()
        alloc_man4 = Alloc_Manager()

        combiners.best_effort("B4_Max_Min", 
                              (lambda g: alloc_man1(g, [app("app1", 10, 'A', 'B', 15), app("app2", 1, 'A', 'B', 5), app("app3", 0.5, 'A', 'C', 10)], B4_Max_Min_Fairshare())),
                              (lambda g: alloc_man2(g, [app("app4", 8, 'C', 'D', 5), app("app5", 1, 'A', 'F', 5), app("app6", 2.5, 'B', 'C', 10)], B4_Max_Min_Fairshare())),
                              (lambda g: alloc_man3(g, [app("app7", 1, 'D', 'E', 2), app("app8", 1, 'E', 'F', 5)], B4_Max_Min_Fairshare())),
                              (lambda g: raiseEx ("A<->B Link Out of Capacity") if g.edge['A']['B']['weight'] == 0 else g),
                              (lambda g: alloc_man4(g, [app("app9", 1, 'B', 'D', 4)], B4_Max_Min_Fairshare())))(graph)

        self.assertEqual(round((alloc_man1.get_flowgroup_by_id("FLWG-AB")).allocated), 20)
        self.assertEqual(round((alloc_man1.get_flowgroup_by_id("FLWG-AC")).allocated), 8)
        self.assertEqual(round((alloc_man2.get_flowgroup_by_id("FLWG-CD")).allocated, 2), 1.75)
        self.assertEqual(round((alloc_man2.get_flowgroup_by_id("FLWG-AF")).allocated, 2), 2)
        self.assertEqual(round((alloc_man2.get_flowgroup_by_id("FLWG-BC")).allocated, 2), 0.25)
        self.assertEqual(round((alloc_man3.get_flowgroup_by_id("FLWG-DE")).allocated), 0)
        self.assertEqual(round((alloc_man3.get_flowgroup_by_id("FLWG-EF")).allocated), 3)
        self.assertEqual(round((alloc_man4.get_flowgroup_by_id("FLWG-BD")).allocated), 4)


def build_graph():
    g = nx.Graph()

    nodeA = g.add_node('A')
    nodeB = g.add_node('B')
    nodeC = g.add_node('C')
    nodeD = g.add_node('D')
    nodeE = g.add_node('E')
    nodeF = g.add_node('F')

    g.add_edge('A', 'B', weight=7)  
    g.add_edge('A', 'C', weight=9)
    g.add_edge('A', 'F', weight=14)  
    g.add_edge('B', 'C', weight=10)
    g.add_edge('B', 'D', weight=15)
    g.add_edge('C', 'D', weight=11)
    g.add_edge('C', 'F', weight=6)
    g.add_edge('D', 'E', weight=6)
    g.add_edge('E', 'F', weight=9)

    return g

if __name__ == '__main__':

    unittest.main()

