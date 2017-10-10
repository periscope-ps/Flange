from lace.logging import trace
from unis import Runtime
from unis.models import Node as uNode, Path as uPath

from flange import settings
from flange.exceptions import ResolutionError
from flange.primitives._base import fl_object


class _resolvable(fl_object):
    __fl_rt__ = Runtime(settings.SOURCE_HOSTS)
    
    def __new__(cls, *args, **kwargs):
        if len(args) and isinstance(args[0], _resolvable):
            args[0] = args[0].__fl_members__
        obj = super().__new__(cls)
        obj.__fl_type__ = cls.__name__
        return obj
    
    def __fl_init__(self, query):
        if isinstance(query, set):
            self.__fl_members__ = query
        else:
            self.__fl_members__ = set(self.__fl_rt__.nodes.where(query))
    
    @trace.debug("resolvable")
    def __exists__(self, candidates):
        for c in candidates:
            yield c
    
    @trace.debug("resolvable")
    def __forall__(self, candidates):
        for c in candidates:
            yield c

class node(_resolvable):
    @property
    def __fl_fringe__(self):
        if hasattr(self, "__fl_fringe_cache__"):
            return self.__fl_fringe_cache__
        result = set()
        for node in self.__fl_members__:
            for port in node.ports:
                if port.link.directed:
                    if port.link.endpoints.source.node == node:
                        if not port.link.endpoints.sink.node in self.__fl_members__:
                            result.add(port)
                else:
                    if port.link.endpoints[0].node == node:
                        if not port.link.endpoints[1].node in self.__fl_members__:
                            result.add(port)
                    else:
                        if not port.link.endpoints[0].node in self.__fl_members__:
                            result.add(port)
        self.__fl_fringe_cache__ = result
        return result
        
    def __exists__(self, candidates):
        nodes = list(candidates)
        if nodes:
            if len(nodes) == 1:
                yield set([nodes[0]])
            else:
                result = uNode()
                result.virtual = True
                result.ports = self.__fl_fringe__
                yield set([result])
                
    def __union__(self, other):
        if isinstance(other, node):
            return node(self.__fl_members__ | other.__fl_members__)
        else:
            raise TypeError("Cannot perform union on node and {}".format(type(other.__fl_type__)))
    
    def __intersection__(self, other):
        if isinstance(other, node):
            return node(self.__fl_members__ & other.__fl_members__)
        else:
            raise TypeError("Cannot perform intersection on node and {}".format(type(other.__fl_type__)))
    
    def __complement__(self):
        return node(lambda x: x not in self.__fl_members__)
    
    def __raw__(self):
        return self.__fl_members__
    
class flow(_resolvable):
    def __fl_init__(self, query):
        self.__fl_query__ = query
    def __raw__(self):
        return self.__fl_members__
    
    @property
    def __fl_members__(self):
        if hasattr(self, "__fl_cache__"):
            for member in self.__fl_cache__:
                yield member
        else:
            cache = []
            for member in self.__fl_query__():
                member = set([uPath({"directed": True, "hops": member})])
                cache.append(member)
                yield member
            self.__fl_cache__ = cache
    
    def __union__(self, other):
        def _union():
            for x in self.__fl_members__:
                yield x
            for y in other.__fl_members__:
                yield y
        return flow(_union)
        
    def __intersection__(self, other):
        def _inter():
            for x in self.__fl_members__:
                for y in other.__fl_members__:
                    yield x | y
        return flow(_inter)
    
    def __complement__(self):
        raise TypeError("Unsupported type")
    
class function(node):
    def __init__(self, name):
        if isinstance(name, list):
            name = "_".join([x.name for x in name])
        self.name = name
    def __fl_init__(self, query):
        self.__fl_members__ = self.__fl_rt__.nodes.where(lambda x: hasattr(x, "properties") and hasattr(x.properties, "executes"))
        
    @trace.debug("Function")
    def __exists__(self, candidates):
        for node in candidates:
            print("here")
            if node.properties.executes == "python":
                yield node
