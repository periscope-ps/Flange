from collections import defaultdict
from lace.logging import trace
from unis.models import Node, Link
from functools import reduce

from flange import utils
from flange.exceptions import ResolutionError
from flange.primitives._base import fl_object
from flange.primitives.internal import Path, PathError

LOOPCOUNT = 3

class _resolvable(fl_object):
    def __init__(self):
        self.annoations = {}
    def __fl_next__(self):
        raise NotImplementedError()
    def get_annoations(self):
        return self.annoations

def _ctx(fl_object):
    def __init__(self, wrapped, attr):
        self._in, self._attr = wrapped, attr
        self.annotations = {}
    def __getattr__(self, n):
        if hasattr(self._in, n):
            return object.__getattribute__(self._in, n)
        else:
            raise AttributeError("'{}' object has no attribute '{}'".format(self._in, n))
    def __eq__(self, other):
        self.annotations[self._attr] = other

    def get_annotations(self):
        return {**self.annoations, **self._in.get_annoations()}
class query(_resolvable):
    @trace.debug("query")
    def __init__(self, q):
        self.annotations = {}
        self.rejected = []
        self.__fl_members__ = q if isinstance(q, set) else set(utils.runtime().nodes.where(q))

    def __getattr__(self, n):
        return _ctx(self, n)
        
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
    def __fl_gather__(self):
        return self.__fl_next__()
    
    @trace.debug("query")
    def __union__(self, other):
        if isinstance(other, query):
            result = query(self.__fl_members__ | other.__fl_members__)
        else:
            result = query(self.__fl_members__)
        result.annotations = {**self.get_annoations(), **other.get_annoations()}
    
    @trace.debug("query")
    def __intersection__(self, other):
        if isinstance(other, query):
            result = query(self.__fl_members__ & other.__fl_members__)
        else:
            result = query(self.__fl_members__)
        result.annoations = {**self.get_annoations(), **other.get_annotations()}
        return result

    @trace.debug("query")
    def __complement__(self):
        return query(lambda x: x not in self.__fl_members__)

class flow(_resolvable):
    class _gather(object):
        def __init__(self, sink, max_congestion):
            self.max_congestion, self.sink, self.weights = max_congestion, sink, defaultdict(lambda: 0)
        
        def _next_node(self, port):
            ends, direct = port.link.endpoints, port.link.directed
            if direct:
                return ends.sink if port == ends.source else None
            else:
                return ends[1] if port == ends[0] else ends[0]

        def accept(self, path):
            for l in filter(lambda x: isinstance(x, Link), path):
                self.weights[l] += 1
            
        def getpath(self, source):
            loops, ccount, fringe, lfringe, rnt = 0, 1, [[source]], [], defaultdict(list)
            visits = defaultdict(lambda: 0)
            while loops < LOOPCOUNT and (fringe or lfringe):
                if not fringe:
                    if ccount < self.max_congestion:
                        fringe, ccount = rnt[ccount], ccount + 1
                    else:
                        fringe, lfringe, loops = lfringe, [], loops + 1
                    fringe = sorted(fringe, key=lambda x: sum([self.weights[l] for l in x if isinstance(l, Link)]))
                else:
                    path = fringe.pop(0)
                    for port in path[-1].ports:
                        if not hasattr(port, "link"): continue
                        eport = self._next_node(port)
                        if eport:
                            new_path = path[:] + [port, port.link, eport, eport.node]
                            visits[eport.node] += 1
                            if self.weights[port.link] < ccount:
                                if eport.node in self.sink:
                                    yield new_path
                                (lfringe if visits[eport.node] > loops+1 else fringe).append(new_path)
                            else:
                                rnt[self.weights[port.link]].append(new_path)

    @trace.debug("flow")
    def __init__(self, source, sink, hops):
        self.__fl_source__, self.__fl_sink__, self.__fl_hops__ = source, sink, hops
        self.negation = False
        self.rejected = []

    @trace.debug("flow")
    def _getpaths(self, source=None):
        source, sink = source or self.__fl_source__.__fl_members__, self.__fl_sink__
        result, loops = [], 0
        
        fringe,lfringe = [[x] for x in source], []
        
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
                        yield Path(path, negation=self.negation)
                    f.append(path)
    
    @trace.debug("flow")
    def __fl_next__(self):
        for path in self._getpaths():
            try:
                i, p, subpaths = 0, path, []
                for rule in self.__fl_hops__:
                    subpath, p = p.pathsplit(rule)
                    i += len(subpath) - 1
                    if isinstance(rule.sink, function):
                        if not any([fn.name == rule.sink.name for fn in path.annotations[i]]):
                            path.annotations[i].append(rule.sink)
                    subpaths.append(subpath)
                if reduce(lambda p,rule: p.pathsplit(rule)[1], self.__fl_hops__, path):
                    yield set([path])
            except PathError:
                self.rejected.append(path)

    @trace.debug("flow")
    def __fl_gather__(self):
        paths = []
        candidates = self._gather(self.__fl_sink__.__fl_members__, len(self.__fl_source__.__fl_members__) + 1)
        for source in self.__fl_source__.__fl_members__:
            for path in candidates.getpath(source):
                candidate = Path(path, self.negation)
                try:
                    i, r = 0, candidate
                    for rule in self.__fl_hops__:
                        l, r = r.pathsplit(rule)
                        i += len(l) - 1
                        if isinstance(rule.sink, function):
                            if not any([fn.name == rule.sink.name for fn in candidate.annotations[i]]):
                                candidate.annotations[i].append(rule.sink)
                except PathError:
                    continue
                candidates.accept(path)
                paths.append(candidate)
                break
        yield set(paths)

    @trace.debug("flow")
    def __union__(self, other):
        def _union():
            for x in self.__fl_next__():
                yield x
            for y in other.__fl_next__():
                yield y
        result = flow(None, None, [])
        result.__fl_next__ = _union
        return result
        
    @trace.debug("flow")
    def __intersection__(self, other):
        def _inter():
            for x in self.__fl_next__():
                for y in other.__fl_next__():
                    yield x | y
        result = flow()
        result.__fl_next__ = _inter
        return result
    
    @trace.debug("flow")
    def __complement__(self):
        self.negation = not self.negation
        return self
    
class function(query):
    def __init__(self, name):
        if isinstance(name, list):
            name = "_".join([x.name for x in name])
        self.name = name
        _q = lambda x: hasattr(x, "properties") and hasattr(x.properties, "executes") and \
             (x.properties.executes == "*" or name in x.properties.executes)
        self.__fl_members__ = set(utils.runtime().nodes.where(_q))

    def __fl_next__(self):
        _, result = super().__fl_next__()
        return set([("function", (self.name, result))])  # Need a way to embbed name, otherwise going to break a lot of things
