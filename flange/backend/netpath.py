from lace.logging import trace
from unis.models import Node, Path, Port, Link

from flange.exceptions import CompilerError
from flange.primitives.ops import _operation

@trace.info("netpath")
def create_node(node):
    return node

@trace.info("netpath")
def create_path(path):
    result = { "directed": True, "hops": [] }
    for i, (ty, item) in enumerate(path):
        if ty in ["node", "function"]:
            if ty == "function":
                name, item, body = item
            serial = item.to_JSON()
            serial["ports"] = []
            src = None
            dst = None
            if i != 0:
                src_ty, src = path[i-1]
                assert src_ty == "port"
                src = src.to_JSON()
            if i != len(path) - 1:
                dst_ty, dst = path[i+1]
                assert dst_ty == "port"
                dst = dst.to_JSON()
                
            if dst and src:
                rules = src.get("rules", [])
                rules.append({
                    "l4_src": path[1][1].address.address,
                    "l4_dst": path[-2][1].address.address,
                    "of_actions": {
                        "OUTPUT": { "action_type": "OUTPUT", "port": dst["index"] }
                    }
                })
                src["rules"] = rules
            serial["ports"] = list(filter(lambda x: x, [src, dst]))
            if ty == "function":
                rules = serial.get("rules", [])
                exists = False
                for rule in rules:
                    if rule["name"] == name:
                        exists = True
                        break
                if not exists:
                    rules.append({ "name": name, "body": body})
                serial["rules"] = rules
            result["hops"].append(serial)
        elif ty == "link":
            result["hops"].append(item.to_JSON())
    return result

@trace.info("netpath")
def run(program):
    result = []
    for op in program:
        if not isinstance(op, _operation):
            raise SyntaxError("Operation cannot be resolved into graph")
        valid = True
        for delta in op.__fl_next__():
            for element in delta:
                if element[0] == "node":
                    result.append(create_node(element[1]))
                elif element[0] == "flow":
                    result.append(create_path(element[1:]))
            if valid:
                break
    if not result:
        raise CompilerError("No solution found!")

    return result
