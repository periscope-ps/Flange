import json

from functools import reduce
from lace.logging import trace
from unis.models import Node, Port, Link

from flange.exceptions import CompilerError,ResolutionError
from flange.primitives.ops import _operation

@trace.info("netpath")
def create_node(node):
    return node.to_JSON()

@trace.info("netpath")
def create_path(path):
    result = {'directed': True, 'hops': []}
    for i, (ty, item) in enumerate(path):
        name, item, body = item if ty == 'function' else (0,item,0)
        if ty in ['node', 'link']:
            result['hops'].append(item.to_JSON())
            if ty == 'node':
                src = path[i-1][1].to_JSON() if i > 0 else None
                dst = path[i+1][1].to_JSON() if i < len(path) - 1 else None
                result['hops'][-1]['ports'] = [x for x in [src, dst] if x]
    return json.dumps(result)

@trace.info("netpath")
def run(program, env):
    result = []
    for op in program:
        if not isinstance(op, _operation):
            raise SyntaxError("Operation cannot be resolved into graph")
        for delta in op.__fl_next__():
            try:
                delta = reduce(lambda x,mod: mod(x, env), env.get('mods', []), delta)
            except ResolutionError as e:
                continue
            for element in delta:
                if element[0] == "node":
                    result.append(create_node(element[1]))
                elif element[0] == "flow":
                    result.append(create_path(element[1:]))
            break
    if not result:
        raise CompilerError("No solution found!")

    return result
