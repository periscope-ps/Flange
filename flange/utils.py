import re
from unis.models import Node

def find_paths(source, sink):
    for source in source.__fl_members__:
        if source in sink.__fl_members__:
            yield [source], [source, sink]
        fringe = [[source]]
        while fringe:
            origin = fringe.pop(0)
            for port in origin[-1].ports:
                node = None
                path = list(origin[1:])
                path.append(port)
                path.append(port.link)
                if path[-1].directed:
                    if path[-1].endpoints.source == port:
                        path.append(path[-1].endpoints.sink)
                        node = path[-1]
                else:
                    if path[-1].endpoints[0] == port:
                        path.append(path[-1].endpoints[1])
                    else:
                        path.append(path[-1].endpoints[0])
                    node = path[-1].node
                if node and node not in path:
                    path.append(node)
                    path.insert(0, origin[0])
                    if node in sink.__fl_members__:
                        yield path, [ x for x in path if isinstance(x, Node) ][1:-1]
                    else:
                        fringe.append(path)


def grammar(re_str, line, lines, handlers):
    groups = re.match(re_str, line[1])
    if not groups:
        raise SyntaxError("Bad Syntax [line {}] - {}".format(*line))
        
    if groups.group("op") in handlers:
        return handlers[groups.group("op")](line, lines)
    else:
        return handlers["default"](line, lines)
        
