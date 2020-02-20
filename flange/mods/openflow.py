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
def _rule_prio(match):
    priority = 500 + sum([1 for v in match.values() if v])
    priority += sum([1 for k,v in match.items() if v and k in ["ip_src", "ip_dst"]])
    return priority

def _get_matching_rule(port, match, p):
    for i,r in enumerate(port.rules):
        if str(p) != str(getattr(r, 'vlan_priority', "")): continue
        if all([getattr(r, k, None) == v for k,v in match.items() if v]):
            return i
    return None

class _Skip(Exception): pass
class _Delete(Exception): pass
def _create_rule(match, actions, prio):
    return {"vlan_priority": str(prio), 'of_actions': actions, **match}
def _modify_rule(rule, actions):
    if len(rule.of_actions) != len(actions) or \
       rule.of_actions.to_JSON(top=False) != actions:
        rule.of_actions = actions
        return True
    return False

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
                mac_dst = path[-2][1].address.address.strip()
            if ty == 'ipv4':
                ip_dst = path[-2][1].address.address.strip()
        except (AttributeError, ValueError): pass

        return { "l2_src": mac_src,
                 "l2_dst": mac_dst,
                 "ip_src": ip_src,
                 "ip_dst": ip_dst,
                 "src_port": path.properties[0].get("l4_src", None),
                 "dst_port": path.properties[0].get("l4_src", None),
                 "ip_proto": path.properties[0].get("ip_proto", None),
                 "vlan": path.properties[0].get("vlan", None)}

def _insert_rules(path, interest, cb):
    ph = _generate_psudoheader(path)
    for i, v in enumerate(path):
        do_delete = False
        ty, e = v if len(v) == 2 else (v, None)
        if ty == 'port':
            interest.append(e)

            try: actions = cb(v, path.properties[i-1], path[i+1], path[i+2] if len(path) > i+2 else None)
            except _Skip: continue
            except _Delete: do_delete = True

            if not hasattr(e, "rule_actions"): e.extendSchema("rule_actions", {"create": [], "modify": [], "delete": []})
            prio = _rule_prio(ph)
            match = {k:v for k,v in ph.items() if v is not None}
            rule = _get_matching_rule(e, match, prio)
            if rule is None:
                if not do_delete:
                    e.rule_actions.create.append(len(e.rules))
                    e.rules.append(_create_rule(match, actions, prio))
            else:
                if all([rule != v for v in e.rule_actions.create]) and \
                   all([rule != v for v in e.rule_actions.modify]) and \
                   all([rule != v for v in e.rule_actions.delete]):
                    if do_delete:
                        e.rule_actions.delete.append(rule)
                    elif _modify_rule(e.rules[rule], actions):
                        e.rule_actions.modify.append(rule)

def call(solution, cb):
    interest = []
    for path in solution.paths:
        assert path[2][0] == 'port' and path[-2][0] == 'port'
        _insert_rules(path, interest, cb)
    return solution, interest

@only('flow')
def openflow_queue(solution, env):
    def cb(port, props, nxt, nxtnxt):
        if "queue" in props and nxt[0] == 'link':
            if props['queue'].value is None:
                raise _Delete()
            return [_set_queue(props['queue'])]
        raise _Skip()
    return call(solution, cb)

@only('flow')
def openflow_forward(solution, env):
    def cb(port, props, nxt, nxtnxt):
        try:
            if nxt[0] in ['node', 'function'] and nxtnxt:
                actions.append(_forward(nxtnxt[1]))
        except AttributeError:
            raise _Skip()
        return actions
    return call(solution, cb)

@only('flow')
def openflow_mod(solution, env):
    def cb(port, props, nxt, nxtnxt):
        actions = []
        if "queue" in props and nxt[0] == 'link':
            actions.append(_set_queue(props['queue']))
        try:
            if nxt[0] in ['node', 'function'] and nxtnxt:
                actions.append(_forward(nxtnxt[1]))
        except AttributeError:
            raise _Skip()
        return actions
    return call(solution, cb)
