from lace.logging import trace

class Resolvable(object):
    def __init__(self):
        self.__fl_query__ = lambda x: True
        
    @trace.debug("Resolvable")
    def __exists__(self, candidates):
        for c in candidates:
            yield c
    
    

class Node(Resolvable):
    pass

class Flow(Resolvable):
    def __init__(self):
        self.__fl_nodes__ = []
        self.__fl_hops__  = []
    
class Function(Node):
    def __init__(self, name):
        self.name = name
        
    @trace.debug("Function")
    def __exists__(self, candidates):
        for node in candidates:
            if hasattr(node, "properties") and hasattr(node.properties, "executes"):
                if node.properties.executes == "python":
                    yield node
