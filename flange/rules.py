from lace.logging import trace

import flange.primitives as prim
from flange.exceptions import CompilerError

def build_rule(hop):
    if hop[0] != "hop":
        raise CompilerError("Unknown rule type")

    def _getenv(n, p): # CHANGEME
        if n != hop[1][1]:
            raise CompilerError("Flow Query may only reference query variable")
        return p
    
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

    return ("hop", _query(hop[1][3]) if hop[1] else lambda p: True, hop[2], hop[3])

def find_rules(inst):
    if not isinstance(inst, tuple) or not inst:
        return inst
    if inst[0] == "rules":
        return tuple(["rules"] + [build_rule(h) for h in inst[1:]])
    else:
        result = [inst[0]]
        for item in inst[1:]:
            result.append(find_rules(item))
        return tuple(result)


@trace.info("rules")
def run(program, env):
    result = []
    for inst in program:
        result.append(find_rules(inst))
    return tuple(result)
