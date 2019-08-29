import flange.measurements as measure
from flange.measurements._common import _flange_prop
from flange.exceptions import ResolutionError

import math

from unis.models import Node, Port, Link
from collections import defaultdict
from functools import reduce

class PathError(Exception):
    pass

class Path(object):
    tag = "flow"
    def __init__(self, hops, properties=None, negation=False):
        self._path_attrs = {
            "throughput_bps": measure.Builder("throughput", min, math.inf),
            "capacity_mbps": measure.StaticBuilder("capacity", min, math.inf),
            "latency_ms": measure.Builder("histogram-owdelay", sum, 0),
            "l4_src": measure.PropertyBuilder("l4_src"),
            "l4_dst": measure.PropertyBuilder("l4_dst"),
            "ip_proto": measure.PropertyBuilder("ip_proto")
        }
        self.negation = negation
        self.properties = properties or defaultdict(lambda: _flange_prop("<no_prop>"))
        self.hops = hops
        self.annotations = defaultdict(list)
        self.origins = defaultdict(lambda: None)

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
            v = ([self.tag] + self.hops)[n]
            return [(self._get_type(i), i) for i in v] if isinstance(v, list) else (self._get_type(v), v)
        else:
            return self.tag

    def pathsplit(self, rule):
        sources, sinks = rule.source._members, rule.sink._members
        if self._get_type(self.hops[0]) != "node" or self.hops[0] not in sources:
            raise PathError()
        for i, item in enumerate(self.hops):
            if self._get_type(item) == "node" and item in sinks:
                return Path(self.hops[:i+1], self.properties), Path(self.hops[i:], self.properties)
        raise PathError()

    
    def __len__(self):
        return len(self.hops) + 1

    def __iter__(self):
        yield self.tag
        for e in self.hops:
            yield (self._get_type(e), e)

    def __repr__(self):
        return "<Path " + " ".join([v.getCollection().name for v in self.hops]) + ">"

class Terminal(Path):
    tag = "node"
    
class Rule(object):
    def __init__(self, f, source, sink):
        self.filter = f
        self.source = source
        self.sink = sink

class Solution(object):
    def __init__(self, paths, env): self.paths, self.env = paths, env
    def negate(self):
        for v in self.paths: v.negation = not v.negation
    def __and__(a, b):
        for r,attr in b.env.items():
            if r in a.env:
                for k in b.env[r].keys():
                    if k in a.env[r]:
                        for c,v in b.env[r][k].items():
                            if c in ['gt', 'ge']: a.env[r][k][c] = max(a.env[r][k].get(c, float('-inf')), v)
                            elif c in ['lt', 'le']: a.env[r][k][c] = min(env[r][k].get(c, float('inf')), v)
                            elif c == 'eq':
                                if a.env[r][k].get(c, float('inf')) != v:
                                    d = {'n': r.name, 'k': k, 'a': a.env[r][k].get('eq', '<empty>'), 'b': v}
                                    msg = "Cannot unify '{n}.{k} == {a}' and '{n}.{k} == {b}'".format(d)
                                    raise ResolutionError(msg)
                                else: a.env[r][k][c] = v
                            elif c == 'ne':
                                if a.env[r][k].get(c, float('inf')) == v:
                                    d = {'n': r.name, 'k': k, 'a': a.env[r][k].get('ne', '<empty>'), 'b': v}
                                    msg = "Cannot unify '{n}.{k} == {a}' and '{n}.{k} == {b}'".format(d)
                                    raise ResolutionError(msg)
                    else:
                        a.env[r][k] = b.env[r][k]
            else:
                a.env[r] = b.env[r]
        return Solution(a.paths + b.paths, a.env)
