from lace.logging import trace
from unis.models import Node, Port, Link


from flange import utils
from flange.exceptions import ResolutionError
from flange.primitives._base import fl_object

LOOPCOUNT = 3

class _resolvable(fl_object):
    def __fl_next__(self):
        raise NotImplemented()

class query(_resolvable):
    @trace.debug("query")
    def __init__(self, q):
        self.__fl_members__ = q if isinstance(q, set) else set(utils.runtime().nodes.where(q))
    
    @property
    def __fl_fringe__(self):
        if hasattr(self, "__fl_fringe_cache__"):
            return self.__fl_fringe_cache__
        result = set()
        for node in self.__fl_members__:
            for port in node.ports:
                if hasattr(port, "link"):
                    end = None
                    if port.link.directed:
                        if port.link.endpoints.source.node == node:
                            end = port.link.endpoints.sink.node
                    else:
                        if port.link.endpoints[0].node == node:
                            end = port.link.endpoints[1].node
                        else:
                            end = port.link.endpoints[0].node
                    if end and end not in self.__fl_members__:
                       result.add(port)
        self.__fl_fringe_cache__ = result
        return result
        
    @trace.debug("query")
    def __fl_next__(self):
        nodes = self.__fl_members__
        if nodes:
            if len(nodes) == 1:
                yield set([("node", list(nodes)[0])])
            else:
                result = Node()
                result.virtual = True
                result._members = self.__fl_members__
                result.ports = list(self.__fl_fringe__)
                yield set([("node", result)])
    
    @trace.debug("query")
    def __union__(self, other):
        if isinstance(other, query):
            return query(self.__fl_members__ | other.__fl_members__)
        else:
            raise TypeError("Cannot perform union on query and {}".format(type(other.__fl_type__)))
    
    @trace.debug("query")
    def __intersection__(self, other):
        if isinstance(other, query):
            return query(self.__fl_members__ & other.__fl_members__)
        else:
            raise TypeError("Cannot perform intersection on query and {}".format(type(other.__fl_type__)))

    @trace.debug("query")
    def __complement__(self):
        return query(lambda x: x not in self.__fl_members__)


class flow(_resolvable):
    @trace.debug("flow")
    def __init__(self, hops):
        self.__fl_hops__ = hops
    
    @trace.debug("flow")
    def _getpaths(self):
        source = self.__fl_hops__[0]
        sink   = self.__fl_hops__[-1]
        result = []
        loops = 0
        
        fringe,lfringe = [[x] for x in source.__fl_members__], []
        
        while loops < LOOPCOUNT and (fringe or lfringe):
            if not fringe:
                fringe = lfringe
                lfringe = []
                loops += 1
            origin = fringe.pop(0)
            for port in origin[-1].ports:
                if not hasattr(port, "link"):
                    continue
                node = None
                path = list(origin[1:])
                path.append(port)
                path.append(port.link)
                if path[-1].directed:
                    if path[-1].endpoints.source == port:
                        path.append(path[-1].endpoints.sink)
                        node = path[-1]
                else:
                    if path[-1].endpoints[0] == port:
                        path.append(path[-1].endpoints[1])
                    else:
                        path.append(path[-1].endpoints[0])
                    node = path[-1].node
                if node:
                    f = lfringe if node in path else fringe
                    path.append(node)
                    path.insert(0, origin[0])
                    if node in sink.__fl_members__:
                        yield path
                    f.append(path)
    
    @trace.debug("flow")
    def __fl_next__(self):
        for path in self._getpaths():
            stack = list(self.__fl_hops__)
            result = ["flow"]
            for element in path:
                tys = {
                    Node: "node",
                    Port: "port",
                    Link: "link"
                }
                for k, ty in tys.items():
                    if isinstance(element, k):
                        break
                if all([not isinstance(element, k) for k in tys.keys()]):
                    raise CompilerError("Found unknown path element - {}".format(type(element)))
                item = (ty, element)
                if ty == "node":
                    if element in stack[0].__fl_members__:
                        if isinstance(stack[0], function):
                            item = ("function", (stack[0].name, element, "function-body-here"))
                        else:
                            item = ("node", element)
                        stack.pop(0)
                result.append(item)
                
            if not stack:
                yield set([tuple(result)])
    
    @trace.debug("flow")
    def __union__(self, other):
        def _union():
            for x in self.__fl_next__:
                yield x
            for y in other.__fl_next__:
                yield y
        result = flow()
        result.__fl_next__ = _union
        return result
        
    @trace.debug("flow")
    def __intersection__(self, other):
        def _inter():
            for x in self.__fl_next__:
                for y in other.__fl_next__:
                    yield x | y
        result = flow()
        result.__fl_next__ = _inter
        return result
    
    @trace.debug("flow")
    def __complement__(self):
        raise TypeError("Type flow does not support complement")
    
class function(query):
    def __init__(self, name):
        if isinstance(name, list):
            name = "_".join([x.name for x in name])
        self.name = name
        self.__fl_members__ = set(utils.runtime().nodes.where(lambda x: hasattr(x, "properties") and hasattr(x.properties, "executes")))

    def __fl_next__(self):
        _, result = super().__fl_next__()
        return set([("function", self.name, result)])
