from unis.models import Node, Path, Port, Link
from flange.exceptions import CompilerError

def create_path(path):
    result = { "directed": True, "hops": [] }
    for i, node in enumerate(path.hops):
        if isinstance(node, Node):
            serial = node.to_JSON()
            serial["ports"] = []
            src = None
            dst = None
            if i != 0:
                src = path.hops[i-1]
                assert isinstance(src, Port)
                src = src.to_JSON()
            if i != len(path.hops) - 1:
                dst = path.hops[i+1]
                assert isinstance(dst, Port)
                dst = dst.to_JSON()
                
            if dst and src:
                rules = src.get("rules", [])
                rules.append({
                    "l4_src": path.hops[1].address.address,
                    "l4_dst": path.hops[-2].address.address,
                    "of_actions": {
                        "OUTPUT": { "action_type": "OUTPUT", "port": dst["index"] }
                    }
                })
                src["rules"] = rules
            serial["ports"] = list(filter(lambda x: x, [src, dst]))
            result["hops"].append(serial)
        if isinstance(node, Link):
            result["hops"].append(node.to_JSON())
    return result

def run(program):
    result = []
    try:
        for v in program:
            ops = next(v.__resolve__())
            for op in ops:
                if op[0] == 'create':
                    if isinstance(op[1], Path):
                        result.append(create_path(op[1]))
                    if isinstance(op[1], Node):
                        result.append(op[1].to_JSON())
    except StopIteration:
        raise CompilerError("No solution found!")

    return result
