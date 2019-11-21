from lace.logging import trace

import flange.primitives as prim
from flange.exceptions import CompilerError

def build_rule(hop, env):
    if hop[0] != "hop":
        raise CompilerError("Unknown rule type")
    query = None if not hop[1] else hop[1] if hop[1][0] == 'query' else env[hop[1][1]]

    def _getenv(n, p):
        if n != query[1] and n not in env.keys():
            raise CompilerError("Unknown symbol - {}".format(n))
        return p if n == query[1] else env[n]
    
    def _query(inst):
        ops = {
            "and":   lambda p: _query(inst[1])(p) and _query(inst[2])(p),
            "or":    lambda p: _query(inst[1])(p) or _query(inst[2])(p),
            "not":   lambda p: not _query(inst[1])(p),
            "var":   lambda p: _getenv(inst[1], p),
            "+":     lambda p: _query(inst[1])(p) + _query(inst[2])(p),
            "-":     lambda p: _query(inst[1])(p) - _query(inst[2])(p),
            "/":     lambda p: _query(inst[1])(p) / _query(inst[2])(p),
            "*":     lambda p: _query(inst[1])(p) * _query(inst[2])(p),
            "%":     lambda p: _query(inst[1])(p) % _query(inst[2])(p),
            "==":    lambda p: _query(inst[1])(p) == _query(inst[2])(p),
            "!=":    lambda p: _query(inst[1])(p) != _query(inst[2])(p),
            ">":     lambda p: _query(inst[1])(p) > _query(inst[2])(p),
            "<":     lambda p: _query(inst[1])(p) < _query(inst[2])(p),
            ">=":    lambda p: _query(inst[1])(p) >= _query(inst[2])(p),
            "<=":    lambda p: _query(inst[1])(p) <= _query(inst[2])(p),
            "index": lambda p: prim.lift_type(_query(inst[1])(p)[_query(inst[2])(p)]),
            "attr":  lambda p: prim.lift_type(getattr(_query(inst[2])(p), inst[1][1]))
        }
        return ops[inst[0]] if isinstance(inst, tuple) else lambda p: inst

    return ("hop", _query(query[3]) if query else lambda p: True, hop[2], hop[3])

def find_rules(inst, env):
    if not isinstance(inst, tuple) or not inst:
        return inst
    if inst[0] == "rules":
        return tuple(["rules"] + [build_rule(h, env) for h in inst[1:]])
    else:
        result = [inst[0]]
        for item in inst[1:]:
            result.append(find_rules(item, env))
        return tuple(result)

def build_env(program):
    env = {}
    for inst in program:
        if inst[0] == 'let':
            env[inst[1]] = inst[2]
        elif inst[0] == 'extern':
            env[inst[1]] = inst[2]
    return env

@trace.info("rules")
def run(program, env):
    result = []
    env = build_env(program)
    for inst in program:
        result.append(find_rules(inst, env))
    return tuple(result)
