import logging

from flange.primitives.internal import Path, Solution
from flange.mods.utils import only

def _forward(out_port):
    index = None
    try: index = out_port.properties.vport_number
    except AttributeError: index = out_port.index
    if index is None:
        logging.getLogger('flange.OF').warn("No compatible index on OF port")
        raise AttributeError("No compatible index on OF port")
    return { "OUTPUT": { "action_type": "OUTPUT", "port": index }}

def _set_queue(queue):
    return { "SET_QUEUE": { "action_type": "SET_QUEUE", "queue_id": queue.value }}

# TODO: Research actual priority hash for this
def _rule_prio(rule):
    priority = 500 + sum([1 for v in rule['match'].values() if v])
    priority += sum([1 for k,v in rule['match'].items() if v and k in ["ip_src", "ip_dst"]])
    return priority

def _get_matching_rule(port, rule, p):
    for i,r in enumerate(port.rules):
        if str(p) != getattr(r, 'vlan_priority', None): continue
        if all([getattr(r, k, None) == v for k,v in rule['match'].items() if v]):
            return i
    return None

def _add_rules(port, rule):
    if not hasattr(port, "rule_actions"): port.extendSchema("rule_actions", {"create": [], "modify": []})
    prio = _rule_prio(rule)
    index = _get_matching_rule(port, rule, prio)
    match = {k:v for k,v in rule['match'].items() if v is not None}
    if index is None:
        if len(port.rules) not in port.rule_actions.create:
            port.rule_actions.create.append(len(port.rules))
        port.rules.append({"vlan_priority": str(prio), 'of_actions': [], **match})
        active = port.rules[-1]
    else:
        if any([index == v for v in port.rule_actions.create]): return
        active = port.rules[index]
        for a in active.of_actions:
            if a.to_JSON(top=False) == rule['action']:
                return

        if all([index != v for v in port.rule_actions.modify]) and \
           any([index == v for v in port.rule_actions.create]) and \
           index not in port.rule_actions.modify:
            port.rule_actions.modify.append(index)

    active.of_actions.append(rule['action'])

def _generate_psudoheader(path, prev=None):
    if prev:
        # TODO: progressive psudoheader generation
        return prev
    else:
        mac_src = mac_dst = ip_src = ip_dst = None
        try:
            ty = getattr(path[2][1].address, 'type', None)
            if ty  == 'mac':
                mac_src = path[2][1].address.address.strip()
            if ty == 'ipv4':
                ip_src = path[2][1].address.address.strip()
        except (AttributeError, ValueError): pass
        try:
            ty = getattr(path[-2][1].address, 'type', None)
            if ty == 'mac':
                mac_dst = path[2][1].address.address.strip()
            if ty == 'ipv4':
                ip_dst = path[-2][1].address.address.strip()
        except (AttributeError, ValueError): pass

        return { "l2_src": mac_src,
                 "l2_dst": mac_dst,
                 "ip_src": ip_src,
                 "ip_dst": ip_dst,
                 "src_port": path.properties.get("l4_src", None),
                 "dst_port": path.properties.get("l4_src", None),
                 "ip_proto": path.properties.get("ip_proto", None),
                 "vlan": path.properties.get("vlan", None)}

def _insert_rules(path, interest):
    ph = _generate_psudoheader(path)
    for i, v in enumerate(path):
        ty, e = v if len(v) == 2 else (v, None)
        if ty == 'port':
            if path[i+1][0] in ['node', 'function']:
                interest.append(e)

                actions = []
                if "queue" in path.properties:
                    actions.append(_set_queue(path.properties['queue']))
                try:
                    if len(path) > i+2:
                        actions.append(_forward(path[i+2][1]))
                except AttributeError:
                    continue

                for action in actions:
                    _add_rules(e, {"match": ph, "action": action})

@only('flow')
def openflow_mod(solution, env):
    interest = []
    for path in solution.paths:
        assert path[2][0] == 'port' and path[-2][0] == 'port'
        _insert_rules(path, interest)
    return solution, interest
