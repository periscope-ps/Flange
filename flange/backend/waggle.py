from collections import defaultdict

from lace.logging import trace
from unis.models import Node, Port, Link

def create_node(item, result):
    if hasattr(item, "functions"):
        for cat in ['create', 'delete', 'modified']:
            for f in getattr(item.functions, cat, []):
                result[cat][item.name][f.name] = f.configuration.to_JSON(top=False)

def create_path(path, result):
    for i, (ty, item) in enumerate(path):
        name, item, body = item if ty == 'function' else (0,item,0)
        if ty == 'node' and hasattr(item, 'functions'):
            for cat in ['create', 'delete', 'modified']:
                for f in getattr(item.functions, cat, []):
                    result[cat][item.name][f.name] = f.configuration.to_JSON(top=False)

@trace.info("netpath")
def run(solutions, env):
    result = {'create': defaultdict(dict), 'delete': defaultdict(dict), 'modified': defaultdict(dict)}
    for solution in solutions:
        for element in solution.paths:
            if element[0] == "node":
                create_node(element[1], result)
            elif element[0] == "flow":
                create_path(element[1:], result)

    return {'create': dict(result['create']),
            'delete': dict(result['delete']),
            'modified': dict(result['modified'])}
