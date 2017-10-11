from copy import copy
from lace.logging import trace

import flange.primitives as prim

from flange import utils
from flange.utils import monad, diad, nimp, recur


@trace.info("buildpaths")
def build_query(inst, env):
    @trace.debug("buildpaths.build_query")
    def _f(x):
        _env = copy(env)
        _env[inst[1]] = x
        try:
            return construct(inst[3], _env)
        except AttributeError:
            return False
            
    result = prim.query(_f)
    if inst[2]:
        return result.__intersection__(construct(inst[1], env))
    return result

@trace.info("buildpaths")
def construct(inst, env):
    def _curry(inst):
        return construct(inst, env)
    ops = {
        "var":   lambda inst: env.get(inst[1], prim.function(inst[1])),
        "+":     diad(lambda a,b: a.__add__(b), _curry),
        "-":     diad(lambda a,b: a.__sub__(b), _curry),
        "/":     diad(lambda a,b: a.__div__(b), _curry),
        "*":     diad(lambda a,b: a.__mult__(b), _curry),
        "%":     diad(lambda a,b: a.__mod__(b), _curry),
        "and":   diad(lambda a,b: a.__intersection__(b), _curry),
        "or":    diad(lambda a,b: a.__union__(b), _curry),
        "not":   monad(lambda a: a.__complement__(), _curry),
        "query": lambda inst: build_query(inst, env),
        "flow":  lambda inst: prim.flow([construct(x, env) for x in inst[1:]]),
        "==":    diad(lambda a,b: a.__eq__(b), _curry),
        "!=":    diad(lambda a,b: a.__ne__(b), _curry),
        ">":     diad(lambda a,b: a.__gt__(b), _curry),
        ">=":    diad(lambda a,b: a.__ge__(b), _curry),
        "<":     diad(lambda a,b: a.__lt__(b), _curry),
        "<=":    diad(lambda a,b: a.__le__(b), _curry),
        "index": lambda inst: utils.lift_type(_curry(inst[1])[_curry(inst[2])]),
        "attr":  lambda inst: utils.lift_type(getattr(_curry(inst[2]), inst[1][1])),
        "exists": lambda inst: prim.exists(construct(inst[1], env)),
        "forall": lambda inst: prim.exists(construct(inst[1], env))
    }
    if isinstance(inst, tuple):
        return ops[inst[0]](inst)
    return inst


@trace.debug("buildpaths")
def _build_env(insts):
    env, deps = utils.build_dep_tree(insts)
    while deps:
        closer = False
        keys = list(deps.keys())
        for k in keys:
            if not deps[k]:
                closer = True
                env[k] = construct(env[k], env)
                for _,v2 in deps.items():
                    if k in v2:
                        v2.remove(k)
                del deps[k]
        if not closer:
            raise DependencyError("Co-dependent variables found, cannot resolve")
            
    return env

@trace.info("buildpaths")
def run(insts):
    result = []
    env = _build_env(insts)
    for inst in insts:
        if inst[0] != "let":
            result.append(construct(inst, env))
    return result
