

class Resolvable(object):
    def __init__(self):
        self.__fl_query__ = lambda x: True
        
    def __exists__(self, candidates):
        return next(candidates)
    
    

class Node(Resolvable):
    pass

class Flow(Resolvable):
    def __init__(self):
        self.__fl_nodes__ = []
        self.__fl_hops__  = []
    
class Function(Node):
    def __init__(self, name):
        self.name = name
        
    def __exists__(self, candidates):
        for node in candidates:
            if node.properties.executes == "python":
                return node
