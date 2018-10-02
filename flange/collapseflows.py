from lace.logging import trace

"""
Native ast representations for flows are
recursive, but the implication of a flow
type is iterative.  collapseflows 
flattens the flow ast node.

(flow f1 a (flow f2 b c))
=>
(flow a c
  (rules
    (hop f1 a b)
    (hop f2 b c)))
"""

@trace.info("collapseflows")
def build_flow(flow):
    @trace.debug("collapseflow.build_flow")
    def _get_rules(item):
        if item[0] == "flow":
            nxt = item[3][2] if item[3][0] == "flow" else item[3]
            rest, last = _get_rules(item[3])
            return [("hop", item[1], item[2], nxt)] + rest, last
        else:
            return [], item

    hops, last = _get_rules(flow)
    return ("flow", flow[2], last, tuple(["rules"] + hops))

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
