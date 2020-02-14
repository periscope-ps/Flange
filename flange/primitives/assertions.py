from flange import utils
from flange.primitives.resolvable import _resolvable
from flange.primitives.internal import Path, Terminal, PathError, Solution
from flange.exceptions import ResolutionError

from collections import defaultdict
from functools import reduce
from lace.logging import trace
from unis.models import Link

LOOPCOUNT = 2

class assertion(_resolvable): pass

@trace("flange.prim")
class Flow(assertion):
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

    def __init__(self, source, sink, hops):
        self._src, self._snk, self._hops = source, sink, hops
        self.negation = False

    def _getpaths(self):
        src, snk = self._src._members, self._snk._members
        if not snk: return
        
        result, loops = [], 0
        fringe,lfringe = [[x] for x in src], []
        while loops < LOOPCOUNT and (fringe or lfringe):
            if not fringe:
                fringe, lfringe, loops = lfringe, [], loops + 1
            origin = fringe.pop(0)
            for port in origin[-1].ports:
                node, path = None, list(origin[1:])
                try:
                    path.extend([port, port.link])
                    link, ep = path[-1], path[-1].endpoints
                except AttributeError: continue
                
                if link.directed and ep.source == port:
                    path.append(ep.sink)
                    node = ep.sink.node
                elif not link.directed:
                    path.append(ep[0 if ep[1] == port else 1])
                    node = path[-1].node
                if node:
                    f = lfringe if node in path else fringe
                    path.append(node)
                    path.insert(0, origin[0])
                    if node in snk:
                        yield Path(path, negation=self.negation)
                    f.append(path)

    def resolve(self):
        for path in self._getpaths():
            try:
                i, p, = 0, path
                for rule in self._hops:
                    subpath, p = p.pathsplit(rule)
                    if not rule.filter(subpath): break
                    path.merge_properties(subpath, i)
                    i += len(subpath) - 1
                    path.origins[i] = rule.sink
                    if isinstance(rule.sink, Function):
                        if not any([fn.name == rule.sink.name for fn in path.annotations[i]]):
                            path.annotations[i].append(rule.sink)
                yield Solution([path], {})
            except PathError: pass

    def gather(self):
        paths = []
        candidates = self._gather(self._snk._members, len(self._src._members) + 1)
        for source in self._src._members:
            for path in candidates.getpath(source):
                candidate = Path(path, self.negation)
                try:
                    i, r = 0, candidate
                    for rule in self._hops:
                        l, r = r.pathsplit(rule)
                        i += len(l) - 1
                        if isinstance(rule.sink, Function):
                            if not any([fn.name == rule.sink.name for fn in candidate.annotations[i]]):
                                candidate.annotations[i].append(rule.sink)
                except PathError:
                    continue
                candidates.accept(path)
                paths.append(candidate)
                break
        yield Solution(paths, {})

    def __complement__(self):
        self.negation = not self.negation
        return self

@trace("flange.prim")
class Query(assertion):
    def __init__(self, q):
        self._members = q if isinstance(q, set) else set(utils.runtime().nodes.where(q))
        self._cache, self.negation = None, False
    def __getattr__(self, n): return Environment(self, n)
    def resolve(self):
        if self._members:
            yield Solution([Terminal([m], self.negation) for m in self._members], {})
    def __complement__(self): return Query(lambda x: x not in self._members)
    
@trace("flange.prim")
class Function(Query):
    def __init__(self, name):
        self.name = name
        _q = lambda x: hasattr(x, "properties") and hasattr(x.properties, "executes") and \
             (x.properties.executes == "*" or all([n in x.properties.executes for n in name]))
        self._members = set(utils.runtime().nodes.where(_q))

    def resolve(self):
        try: result = next(super().resolve())
        except StopIteration: raise ResolutionError("No virtual function nodes found in graph")
        path = Path([result], negation=self.negation)
        yield Solution([path], {})

@trace("flange.prim")
class Environment(assertion):
    def __init__(self, target, name):
        self._target, self._n = target, name
        self._v = None
    def __eq__(self, v):
        self._v = {'eq': getattr(v, '__raw__', lambda: v)()}
        return self
    def __ne__(self, v):
        self._v = {'ne': v}
        return self
    def __gt__(self, v):
        self._v = {'gt': v}
        return self
    def __ge__(self, v):
        self._v = {'ge': v}
        return self
    def __lt__(self, v):
        self._v = {'lt': v}
        return self
    def __le__(self, v):
        self._v = {'le': v}
        return self
    
    def resolve(self):
        if not self._v:
            raise SyntaxError("'<value>.{}' must have a test value".format(self._n))
        yield Solution([], {self._target: { self._n: self._v }})
