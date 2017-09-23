from flange import settings
from flange import primitives as prim
from lace.logging import trace
from unis import Runtime
from unis.models import Path, Node

rt = None

class DependencyError(Exception):
    pass
class ResolutionError(Exception):
    pass

@trace.debug("naiveflow")
def _build_query(q):
    def f(x):
        ops = {
            "and":    lambda q: _f(q[1]) and _f(q[2]),
            "or":     lambda q: _f(q[1]) or _f(q[2]),
            "not":    lambda q: not _f(q[1]),
            "==":     lambda q: _f(q[1]) == _f(q[2]),
            "!=":     lambda q: _f(q[1]) != _f(q[2]),
            ">":      lambda q: _f(q[1]) > _f(q[2]),
            ">=":     lambda q: _f(q[1]) >= _f(q[2]),
            "<":      lambda q: _f(q[1]) < _f(q[2]),
            "<=":     lambda q: _f(q[1]) <= _f(q[2]),
            "+":      lambda q: _f(q[1]) + _f(q[2]),
            "-":      lambda q: _f(q[1]) - _f(q[2]),
            "/":      lambda q: _f(q[1]) / _f(q[2]),
            "*":      lambda q: _f(q[1]) * _f(q[2]),
            "%":      lambda q: _f(q[1]) % _f(q[2]),
            "index":  lambda q: _f(q[1])[_f(q[2])],
            "attr":   lambda q: hasattr(_f(q[1]), q[2][1]) and getattr(_f(q[1]), q[2][1]),
            "var":    lambda q: hasattr(x, q[1]) and getattr(x, q[1]),
            "bool":   lambda q: q[1] == "True",
            "number": lambda q: q[1],
            "string": lambda q: q[1],
            "empty":  lambda q: None
        }
        def _f(q):
            return ops[q[0]](q)
        return _f(q)
    return f

@trace.debug("naiveflow")
def _build_func(inst):
    func = prim.Function(inst[1])
    func.__fl_query__ = lambda x: hasattr(x, "properties") and hasattr(x.properties, "executes")
    return func

@trace.debug("naiveflow")
def _build_node(inst, env):
    node = prim.Node()
    node.__fl_query__ = _build_query(inst[1])
    return node
    
@trace.debug("naiveflow")
def _build_flow(inst, env):
    nodes = []
    hops  = []
    while inst[0] == "flow":
        if inst[2][0] == "query":
            nodes.append(_build_node(inst[2], env))
        elif inst[2][0] == "var":
            nodes.append(env.get(inst[2][1], _build_func(inst[2][1])))
        else:
            raise TypeError("Unknown type applied to flow")
        hops.append(inst[1])
        inst = inst[3]
    if inst[0] == "query":
        nodes.append(_build_node(inst, env))
    elif inst[0] == "var":
        end = env.get(inst[1], _build_func(inst[1]))
        if isinstance(end, prim.Node):
            nodes.append(end)
        else:
            raise TypeError("Unknown type applied to flow")
    flow = prim.Flow()
    flow.__fl_hops__ = hops
    flow.__fl_nodes__ = nodes
    return flow
    
@trace.debug("naiveflow")
def _resolve(inst, env):
    def dyad(f):
        return lambda: f(_resolve(inst[1], env), _resolve(inst[2], env))
    def monad(f):
        return lambda: f(_resolve(inst[1]))
    def _nimp(msg):
        raise NotImplemented(msg)
    ops = {
        "+": dyad(lambda x,y: x + y),
        "-": dyad(lambda x,y: x - y),
        "/": dyad(lambda x,y: x / y),
        "*": dyad(lambda x,y: x / y),
        "%": dyad(lambda x,y: x % y),
        "or": dyad(lambda x,y: x or y),
        "and": dyad(lambda x,y: x and y),
        "==": dyad(lambda x,y: x == y),
        "!=": dyad(lambda x,y: x != y),
        "<": dyad(lambda x,y: x < y),
        "<=": dyad(lambda x,y: x <= y),
        ">": dyad(lambda x,y: x > y),
        ">=": dyad(lambda x,y: x >= y),
        "not": monad(lambda x: not x),
        "app": _nimp,
        "index": dyad(lambda x,y: x[y]),
        "attr": _nimp,
        "var": lambda: env.get(inst[1], _build_func(inst)),
        "bool": lambda: inst[1] == "True",
        "number": lambda: inst[1],
        "string": lambda: inst[1],
        "empty": lambda: None,
        "query": lambda: _build_node(inst, env),
        "flow": lambda: _build_flow(inst, env),
        "list": lambda: [_resolve(x, env) for x in _list[1:]],
        "path": _nimp
    }
    return ops[inst[0]]()

@trace.debug("naiveflow")
def _build_env(program):
    def _find_deps(inst):
        if isinstance(inst, tuple):
            if inst[0] == "query":
                return []
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
            return None
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

@trace.debug("naiveflow")
def _find_routes(source, sink):
    fringe = [[source]]
    while fringe:
        origin = fringe.pop(0)
        for port in origin[-1].ports:
            node = None
            path = list(origin)
            path.append(port)
            path.append(port.link)
            if path[-1].directed:
                if path[-1].endpoints.source == port:
                    path.append(path[-1].endpoints.sink)
                    path.append(path[-1].node)
                    node = path[-1]
            else:
                if path[-1].endpoints[0] == port:
                    path.append(path[-1].endpoints[1])
                    path.append(path[-1].node)
                else:
                    path.append(path[-1].endpoints[0])
                    path.append(path[-1].node)
                node = path[-1]
            if node:
                if node == sink:
                    yield path
                elif len(path) < settings.MAX_DEPTH:
                    fringe.append(path)
    raise ResolutionError("No acceptable routes selected")

@trace.debug("naiveflow")
def _exists(obj):
    if isinstance(obj, prim.Node):
        candidates = rt.nodes.where(obj.__fl_query__)
        try:
            return [next(obj.__exists__(candidates))]
        except StopIteration:
            raise ResolutionError("Node does not exist")
    if isinstance(obj, prim.Flow):
        # This is the hard part
        flows = []
        i = 0
        bookends = [0, 0]
        while i < len(obj.__fl_nodes__) - 1:
            if not isinstance(obj.__fl_nodes__[i+1], prim.Function):
                bookends[1] = i + 1
                pair = (_exists(obj.__fl_nodes__[bookends[0]])[0], _exists(obj.__fl_nodes__[bookends[1]])[0])
                paths = obj.__exists__(_find_routes(*pair))
                for path in paths:
                    _good = True
                    nodes = list(filter(lambda x: isinstance(x, Node), path))
                    for func in obj.__fl_nodes__[bookends[0]+1:bookends[1]]:
                        _good = False
                        for _ in func.__exists__(nodes):
                            _good = True
                            break
                        if not _good:
                            break
                    if _good:
                        flows.append(Path({"directed": True, "hops": path}))
                        break
                bookends[0] = bookends[1]
            i += 1
        if isinstance(obj.__fl_nodes__[i], prim.Function):
            raise SyntaxError("Flow may not end in a function")
        
        return flows
            

@trace.info("naiveflow")
def run(program, ext_rt=None):
    global rt
    if not ext_rt:
        rt = Runtime(settings.SOURCE_HOSTS)
    else:
        rt = ext_rt
    flows = []
    env = _build_env(program)
    for inst in program:
        if inst[0] == "exists":
            flows.extend(_exists(_resolve(inst[1], env)))
    
    return flows


if __name__ == "__main__":
    from pprint import pprint
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
