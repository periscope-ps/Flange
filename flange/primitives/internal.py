import flange.measurements as measure

import math

from unis.models import Node, Port, Link
from functools import reduce

class Path(object):
    def __init__(self, hops):
        self._path_attrs = {
            "throughput_mbps": measure.Builder("throughput", min, math.inf),
            "capacity_mbps": measure.StaticBuilder("capacity", min, math.inf),
            "latency_ms": measure.Builder("histogram-rtt", sum, 0)
        }
        
        self.hops = hops

    def __getattr__(self, n):
        if n in self._path_attrs.keys():
            return self._path_attrs[n](self)
        else:
            return super().__getattribute__(n)
            
    def _get_type(self, e):
        tys = {
            Link: "link",
            Port: "port",
            Node: "node"
        }
        return reduce(lambda x,y: tys[y] if isinstance(e, y) else x, tys.keys(), None)

    def __getitem__(self, n):
        if n:
            v = (["flow"] + self.hops)[n]
            return [(self._get_type(i), i) for i in v] if isinstance(v, list) else (self._get_type(v), v)
        else:
            return "flow"

    def __len__(self):
        return len(self.hops) + 1

    def __iter__(self):
        yield "flow"
        for e in self.hops:
            yield (self._get_type(e), e)

    def __repr__(self):
        return "<Path " + " ".join([v.getCollection().name for v in self.hops]) + ">"

class Rule(object):
    def __init__(self, f, source, sink):
        self.filter = f
        self.source = source
        self.sink = sink

    def _find_subpath(self, path):
        result, inpath = [], False
        for item in path:
            ty, ele = item if isinstance(item, tuple) else (None, item)
            if not inpath:
                if ty == "node" and ele in self.source.__fl_members__:
                    inpath = True
            if inpath:
                result.append(ele)
                if ty == "node" and ele in self.sink.__fl_members__:
                    return Path(result)
        return []
    
    def apply(self, path):
        subpath = self._find_subpath(path)
        return subpath and self.filter(subpath)
