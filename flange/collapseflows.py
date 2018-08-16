from lace.logging import trace

@trace.info("collapseflows")
def build_flow(flow):
    @trace.debug("collapseflow.build_flow")
    def _collapse(item):
        if item[0] == "flow":
            result = [item[2]]
            result.extend(_collapse(item[3]))
        else:
            result = [item]
        return result
    
    result = ["flow"]
    result.extend(_collapse(flow))
    return tuple(result)

@trace.info("collapseflows")
def find_flows(inst):
    if not isinstance(inst, tuple) or not inst:
        return inst
    if inst[0] == "flow":
        return build_flow(inst)
    else:
        result = [inst[0]]
        for item in inst[1:]:
            result.append(find_flows(item))
        return tuple(result)

@trace.info("collapseflows")
def run(insts, env):
    result = []
    for inst in insts:
        result.append(find_flows(inst))
    return tuple(result)
