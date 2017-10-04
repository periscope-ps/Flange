import flange.primitives as prim

from flange import utils
from flange.exceptions import DependencyError, ResolutionError, CompilerError


from lace.logging import trace

rt = None


@trace.debug("naiveflow")
def _build_query(token, q, env):
    def f(x):
        def _attr(q):
            if q[2][0] == "var" and q[2][1] == token:
                return hasattr(x, q[1][1]) and getattr(x, q[1][1])
            else:
                return hasattr(_f(q[2]), q[1][1]) and getattr(_f(q[2]), q[1][1])
        ops = {
            "and":      lambda q: _f(q[1]) and _f(q[2]),
            "or":       lambda q: _f(q[1]) or _f(q[2]),
            "not":      lambda q: not _f(q[1]),
            "==":       lambda q: _f(q[1]) == _f(q[2]),
            "!=":       lambda q: _f(q[1]) != _f(q[2]),
            ">":        lambda q: _f(q[1]) > _f(q[2]),
            ">=":       lambda q: _f(q[1]) >= _f(q[2]),
            "<":        lambda q: _f(q[1]) < _f(q[2]),
            "<=":       lambda q: _f(q[1]) <= _f(q[2]),
            "+":        lambda q: _f(q[1]) + _f(q[2]),
            "-":        lambda q: _f(q[1]) - _f(q[2]),
            "/":        lambda q: _f(q[1]) / _f(q[2]),
            "*":        lambda q: _f(q[1]) * _f(q[2]),
            "%":        lambda q: _f(q[1]) % _f(q[2]),
            "index":    lambda q: _f(q[1])[_f(q[2])],
            "attr":     _attr,
            "var":      lambda q: env[q[1]].__raw__(),
            "bool":     lambda q: q[1] == "True",
            "number":   lambda q: q[1],
            "string":   lambda q: q[1],
            "empty":    lambda q: None
        }
        def _f(q):
            result = ops[q[0]](q)
            return result
        return _f(q)
    return f

@trace.debug("naiveflow")
def _build_func(inst):
    func = prim.function(inst[1])
    return func

@trace.debug("naiveflow")
def _build_node(inst, env):
    node = prim.node(_build_query(inst[1], inst[3], env))
    if inst[2]:
        return node.__intersection__(_resolve(inst[2], env))
    return node
    
@trace.debug("naiveflow")
def _build_hops(inst, env):
    nodes = []
    hops = []
    while inst[0] == "flow":
        node = _resolve(inst[2], env)
        if not isinstance(node, prim.node):
            raise TypeError("Flow cannot contain non-node elements")
        nodes.append(_resolve(inst[2], env))
        hops.append(inst[1])
        inst = inst[3]
    node = _resolve(inst, env)
    if isinstance(node, prim.fl_list):
        node = prim.func(node)
    nodes.append(_resolve(inst, env))
    return (nodes, hops)
    
@trace.debug("naiveflow")
def _build_flow(inst, env):
    nodes, hops = _build_hops(inst, env)
    @trace.debug("flowgraph")
    def _q():
        for path, pnodes in utils.find_paths(nodes[0], nodes[-1]):
            stack = list(nodes[1:-1])
            for node in pnodes:
                if stack:
                    if node in stack[0].__fl_members__:
                        stack.pop(0)
            if not stack:
                yield path
    return prim.flow(_q)
    
@trace.debug("naiveflow")
def _resolve(inst, env):
    def dyad(f):
        return lambda: f(_resolve(inst[1], env), _resolve(inst[2], env))
    def monad(f):
        return lambda: f(_resolve(inst[1], env))
    def _nimp(msg):
        def _f():
            raise NotImplemented(msg)
        return _f
    def _badinst(msg):
        def _f():
            raise SyntaxError("Bad Syntax: Invalid use of instruction - {}".format(msg))
        return _f
    ops = {
        "+": dyad(lambda x,y: x.__add__(y)),
        "-": dyad(lambda x,y: x.__sub__(y)),
        "/": dyad(lambda x,y: x.__div__(y)),
        "*": dyad(lambda x,y: x.__mult__(y)),
        "%": dyad(lambda x,y: x.__mod__(y)),
        "or": dyad(lambda x,y: x.__union__(y)),
        "and": dyad(lambda x,y: x.__intersection__(y)),
        "not": monad(lambda x: x.__complement__()),
        "==": dyad(lambda x,y: x == y),
        "!=": dyad(lambda x,y: x != y),
        "<": dyad(lambda x,y: x < y),
        "<=": dyad(lambda x,y: x <= y),
        ">": dyad(lambda x,y: x > y),
        ">=": dyad(lambda x,y: x >= y),
        "app": _nimp("Function application"),
        "index": dyad(lambda x,y: x.__getitem__(y)),
        "attr": _nimp("Class attributes"),
        "var": lambda: env.get(inst[1], _build_func(inst)),
        "bool": lambda: prim.boolean(inst[1] == "True"),
        "number": lambda: prim.number(inst[1]),
        "string": lambda: prim.string(inst[1]),
        "empty": lambda: _nimp("None"),
        "query": lambda: _build_node(inst, env),
        "flow": lambda: _build_flow(inst, env),
        "list": lambda: prim.fl_list([_resolve(x, env) for x in _list[1:]]),
        "exists": lambda: prim.exists(_resolve(inst[1], env)),
        "forall": lambda: prim.forall(_resolve(inst[1], env)),
        "path": _nimp("Paths"),
    }
    try:
        return ops[inst[0]]()
    except KeyError:
        raise SyntaxError("Bad Syntax: Invalid use of instruction - {}".format(inst[0]))

@trace.debug("naiveflow")
def _build_env(program):
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
            
    while deps:
        closer = False
        keys = list(deps.keys())
        for k in keys:
            if not deps[k]:
                closer = True
                env[k] = _resolve(env[k], env)
                for _,v2 in deps.items():
                    if k in v2:
                        v2.remove(k)
                del deps[k]
        if not closer:
            raise DependencyError("Co-dependent variables found, cannot resolve")
            
    return env

@trace.info("naiveflow")
def run(program, ext_rt=None):
    results = []
    env = _build_env(program)
    for inst in program:
        if inst[0] != "let":
            res = _resolve(inst, env)
            if hasattr(res, "__resolve__"):
                results.append(res)
            else:
                raise CompilerError("Top level operation was not resolvable")
    return results


if __name__ == "__main__":
    from pprint import pprint
    from unis import Runtime
    from unis.models import Node, Port, Link
    rt = Runtime()
    test = [("exists", ("query", ("==", ("var", "name"), ("string", "blah"))))]
    test2 = [("exists", ("flow", [], ("query", ("==", ("var", "name"), ("string", "blah"))), ("query", ("==", ("var", "name"), ("string", "blah2")))))]
    
    try:
        pprint(run(test, rt))
    except ResolutionError as exp:
        print(exp)
    n = Node({"name": "blah"})
    rt.insert(n)
    
    pprint(run(test, rt)[0].to_JSON())
    
    
    n2 = Node({"name": "blah2"})
    rt.insert(n2)
    
    try:
        pprint(run(test2, rt))
    except ResolutionError as exp:
        print(exp)
        
    p1 = Port()
    rt.insert(p1)
    n.ports.append(p1)
    
    p2 = Port()
    rt.insert(p2)
    n2.ports.append(p2)
    
    l = Link()
    l.directed = False
    l.endpoints = [p1, p2]
    rt.insert(l)
    
    p1.node = n
    p2.node = n2
    p1.link = l
    p2.link = l
    
    pprint(run(test2, rt))
