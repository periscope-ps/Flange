import flange.measurements as measure

import math

from unis.models import Node, Port, Link
from functools import reduce

class Path(object):
    def __init__(self, hops):
        self._path_attrs = {
            "throughput_bps": measure.Builder("throughput", min, math.inf),
            "capacity_mbps": measure.StaticBuilder("capacity", min, math.inf),
            "latency_ms": measure.Builder("histogram-owdelay", sum, 0),
            "l4_src": measure.PropertyBuilder("l4_src"),
            "l4_dst": measure.PropertyBuilder("l4_dst")
        }
        self.properties = {}
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

    def subpath(self, sources, sinks):
        result, inpath = [], False
        for item in self.hops:
            ty = self._get_type(item)
            if not inpath:
                if ty == "node" and item in sources:
                    inpath = True
            if inpath:
                result.append(item)
                if ty == "node" and item in sinks:
                    new = Path(result)
                    new.properties = self.properties
                    return new
        return []

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

    def apply(self, path):
        subpath = path.subpath(self.source.__fl_members__, self.sink.__fl_members__)
        return subpath and self.filter(subpath)
