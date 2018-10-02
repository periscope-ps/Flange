
from lace.logging import trace
import flange.primitives as prim

"""
createobjects replaces all of the object ast
leafs with native flange objects.
"""

builtins = {
    "number": prim.number,
    "string": prim.string,
    "bool":   prim.boolean,
    "empty":  prim.empty,
}


@trace.info("createobjects")
def find_objects(inst):
    if not isinstance(inst, tuple) or not inst:
        return inst
    if inst[0] in builtins.keys():
        return builtins[inst[0]](inst[1])
    else:
        result = [inst[0]]
        for item in inst[1:]:
            result.append(find_objects(item))
        return tuple(result)

@trace.info("createobjects")
def run(insts, env):
    result = []
    for inst in insts:
        result.append(find_objects(inst))
    return tuple(result)
