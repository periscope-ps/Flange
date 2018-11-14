import json

from lace.logging import trace
from unis.models import Node, Port, Link


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
def run(changes, env):
    result = []
    for delta in changes:
        for element in delta:
            if element[0] == "node":
                result.append(create_node(element[1]))
            elif element[0] == "flow":
                result.append(create_path(element[1:]))
    return result
