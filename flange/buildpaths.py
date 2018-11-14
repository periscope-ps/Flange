from copy import copy
from lace.logging import trace

import flange.primitives as prim

from flange import utils
from flange.utils import monad, diad, nimp, recur

@trace.info("buildpaths")
def build_query(inst, env):
    env = copy(env)
    env[inst[1]] = inst[1]
    @trace.debug("buildpaths.build_query")
    def _invert(inst):
        ops = {
            "and": lambda: ("or", ("not", inst[1]), ("not", inst[2])),
            "or": lambda: ("and", ("not", inst[1]), ("not", inst[2])),
            "not": lambda: inst[1],
            "==": lambda: ("!=", inst[1], inst[2]),
            "!=": lambda: ("==", inst[1], inst[2]),
            ">": lambda: ("<=", inst[1], inst[2]),
            "<": lambda: (">=", inst[1], inst[2]),
            ">=": lambda: ("<", inst[1], inst[2]),
            "<=": lambda: (">", inst[1], inst[2])
        }
        if isinstance(inst, tuple) and inst[0] in ops:
            return ops[inst[0]]()
        else:
            raise SyntaxError()
        
    @trace.debug("buildpaths.build_query")
    def _q(name, inst):
        def _query(inst):
            ops = {
                "and": lambda: _query(inst[1]).intersection(_query(inst[2])),
                "or": lambda: _query(inst[1]).union(_query(inst[2])),
                "not": lambda: _query(_invert(inst[1])),
                "var": lambda: env.get(inst[1], inst[1]),
                "+": lambda: _query(inst[1]) + _query(inst[2]),
                "-": lambda: _query(inst[1]) - _query(inst[2]),
                "/": lambda: _query(inst[1]) / _query(inst[2]),
                "*": lambda: _query(inst[1]) * _query(inst[2]),
                "%": lambda: _query(inst[1]) % _query(inst[2]),
                "==": lambda: set(utils.runtime().nodes.where({_query(inst[1]): {"eq": _query(inst[2])}})),
                "!=": lambda: (lambda f, x,y: set(f({x: {"gt": y}})).union(set(f({x: {"lt": y}}))))(utils.runtime().nodes.where, _query(inst[1]), _query(inst[2])),
                ">": lambda: set(utils.runtime().nodes.where({_query(inst[1]): {"gt":_query(inst[2])}})),
                "<": lambda: set(utils.runtime().nodes.where({_query(inst[1]): {"lt":_query(inst[2])}})),
                ">=": lambda: set(utils.runtime().nodes.where({_query(inst[1]): {"gte":_query(inst[2])}})),
                "<=": lambda: set(utils.runtime().nodes.where({_query(inst[1]): {"lte":_query(inst[2])}})),
                "index": lambda: _query(inst[1])[_query(inst[2])],
                "attr": lambda: getattr(_query(inst[2]), _query(inst[1])) if _query(inst[2]) != name else _query(inst[1])
            }
            if isinstance(inst, tuple):
                return ops[inst[0]]()
            return getattr(inst, '__raw__', lambda: inst)()
        return _query(inst)
    @trace.debug("buildpaths.build_query")
    def _f(x):
        _env = copy(env)
        _env[inst[1]] = x
        try:
            return construct(inst[3], _env)
        except AttributeError as exp:
            return False
    
    result = prim.query(_q(inst[1], inst[3]))
    if inst[2]:
        return result.__intersection__(construct(inst[2], env))
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
        "flow":  lambda inst: prim.flow(*[construct(x, env) for x in inst[1:]]),
        "rules": lambda inst: [construct(rule, env) for rule in inst[1:]],
        "hop":   lambda inst: prim.Rule(inst[1], *[construct(v, env) for v in inst[2:]]),
        "==":    diad(lambda a,b: a.__eq__(b), _curry),
        "!=":    diad(lambda a,b: a.__ne__(b), _curry),
        ">":     diad(lambda a,b: a.__gt__(b), _curry),
        ">=":    diad(lambda a,b: a.__ge__(b), _curry),
        "<":     diad(lambda a,b: a.__lt__(b), _curry),
        "<=":    diad(lambda a,b: a.__le__(b), _curry),
        "index": lambda inst: prim.lift_type(_curry(inst[1]).__getitem__(_curry(inst[2]))),
        "attr":  lambda inst: prim.lift_type(getattr(_curry(inst[2]), inst[1][1])),
        "exists": lambda inst: prim.exists(construct(inst[1], env)),
        "forall": lambda inst: prim.forall(construct(inst[1], env)),
        "gather": lambda inst: prim.gather(construct(inst[1], env))
    }
    return ops[inst[0]](inst) if isinstance(inst, tuple) else inst
    

@trace.debug("buildpaths")
def _build_env(insts):
    env, deps = utils.build_dep_tree(insts)
    while deps:
        closer = False
        for k in list(deps.keys()):
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
def run(insts, env):
    result = []
    env = _build_env(insts)
    for inst in insts:
        if inst[0] != "let":
            result.append(construct(inst, env))
    return result
