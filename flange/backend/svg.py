from lace.logging import trace

from flange import utils

@trace.info("svg")
def create_path(path):
    rules = []
    for i, (ty, element) in enumerate(path):
        if i == 0 or i == len(path) - 1:
            rules.append((element, ""))
        if ty in ['node', 'function']:
            if ty == 'function':
                name, element, body = element
                rules.append((element, "register stream process - {}".format(name)))
        if i != 0 and i != len(path) - 1 and ty == 'node':
            rules.append((element, "nw_src: {}\nnw_dst: {}\nFORWARD\n> PORT {} TO {}".format(path[1][1].address.address,
                                                                                             path[-2][1].address.address,
                                                                                             path[i -1][1].index, path[i + 1][1].index)))
    return rules

@trace.info("svg")
def run(changes, env):
    rules = []
    
    if not utils.runtime().graph.processing_level:
        utils.runtime().graph.spring(25, 50)

    for delta in changes:
        for element in delta:
            if element[0] == "node":
                if hasattr(element[1], "virtual") and element[1].virtual:
                    for n in element[1]._members:
                        rules.append([(n, "")])
                else:
                    rules.append([(element[1], "")])
            elif element[0] == "flow":
                rules.append(create_path(element[1:]))

    return utils.runtime().graph.svg(rules)
