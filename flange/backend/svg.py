
from lace.logging import trace
from flange import utils
from flange.primitives.ops import _operation


@trace.info("svg")
def create_path(path):
    rules = []
    result = []
    for i, (ty, element) in enumerate(path):
        if ty in ['node', 'function']:
            if ty == 'function':
                name, element, body = item
                rules.append((element, "register stream process - {}".format(name)))
            result.append(element)
        if i != 0 and i != len(path) - 1 and ty == 'node':
            rules.append((element, "l4_src: {}\nl4_dst: {}\nFORWARD\n> PORT {} TO {}".format(path[1][1].address.address,
                                                                                             path[-2][1].address.address,
                                                                                             path[i -1][1].index, path[i + 1][1].index)))
    return result, rules

@trace.info("svg")
def run(program):
    active = []
    rules = []
    
    if not utils.runtime().graph.processing_level:
        utils.runtime().graph.spring(25, 1000)
    
    for op in program:
        if not isinstance(op, _operation):
            raise SyntaxError("Operation cannot be resolved into graph")
        for delta in op.__fl_next__():
            for element in delta:
                if element[0] == "node":
                    active.append([element[1]])
                elif element[0] == "flow":
                    nodes, rule = create_path(element[1:])
                    active.append(nodes)
                    rules.extend(rule)
                    
            break
    return utils.runtime().graph.svg(active, rules)
