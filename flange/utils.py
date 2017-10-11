import re
from unis.models import Node

from lace.logging import trace

import flange.primitives as prim

def diad(app, f):
    return lambda inst: app(f(inst[1]), f(inst[2]))
def monad(app, f):
    return lambda inst: app(f(inst[1]))
def nimp(msg):
    def _f():
        raise NotImplemented(msg)
    return _f
def recur(f):
    def _f(inst):
        result = [inst[0]]
        for arg in inst[1:]:
            result.append(f(arg))
        return tuple(result)
    return _f
@trace.debug("utils")
def lift_type(arg):
    if isinstance(arg, str):
        return prim.string(arg)
    elif isinstance(arg, (int, float)):
        return prim.number(arg)
    elif isinstance(arg, bool):
        return prim.boolean(arg)
    elif isinstance(arg, type(None)):
        return prim.empty(arg)
    else:
        return arg


@trace.debug("utils")
def build_dep_tree(program):
    def _find_deps(inst):
        if inst and isinstance(inst, tuple):
            if inst[0] == "query":
                return _find_deps(inst[3:])
            if inst[0] == "var":
                return [inst[1]]
            else:
                deps = []
                for v in inst[1:]:
                    _new_deps = _find_deps(v)
                    if _new_deps:
                        deps.extend(_new_deps)
                return deps
        else:
            return []
    deps = {}
    env = {}
    for i, inst in enumerate(program):
        if inst[0] == "let":
            if inst[1] in deps:
                raise SyntaxError("{} cannot be rebound [line {}]".format(inst[1], i))
            deps[inst[1]] = _find_deps(inst[2])
            env[inst[1]]  = inst[2]
            
    return env, deps


@trace.info("utils")
def grammar(re_str, line, lines, handlers):
    groups = re.match(re_str, line[1])
    if not groups:
        raise SyntaxError("Bad Syntax [line {}] - {}".format(*line))
        
    if groups.group("op") in handlers:
        return handlers[groups.group("op")](line, lines)
    else:
        return handlers["default"](line, lines)
        
