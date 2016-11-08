

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


