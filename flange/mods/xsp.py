from flange.exceptions import ResolutionError
from flange.primitives.internal import Path

import logging

def xsp_forward(paths, env):
    key_map = {
        "l4_src": "src_port",
        "l4_dst": "dst_port",
        "ip_proto": "ip_proto"
    }

    def _find_rules(rules, src, dst, **kwargs):
        for i,r in enumerate(rules):
            if all([getattr(r, key_map[k], None) == v.value for k,v in kwargs.items()]) and \
               getattr(r, 'ip_src', None) == src and getattr(r, 'ip_dst', None) == dst:
                    yield i
    
    def _insert_rules(e, src, dst, props, annotations):
        result = []
        for i, (ty, s) in enumerate(e):
            if ty == 'port' and len(e) > i+2:
                try: index = e[i+2][1].properties.vport_number
                except AttributeError: index = e[i+2][1].index
                if not index:
                    logging.getLogger('flange.OF').warn("No compatible index on OF port")
                elif e[i+1][0] in ['node', 'function']:
                    matches = list(sorted(_find_rules(s.rules, src, dst, **props), key=lambda x: getattr(s.rules[x], 'priority', 0)))
                    if matches:
                        match = False
                        for a in s.rules[matches[0]].of_actions:
                            try:
                                match = True
                                if a.OUTPUT.port != index:
                                    a.OUTPUT.port = index
                                    s.rules[matches[0]]._fl_action = "modify"
                                    break
                            except (AttributeError, IndexError) as exp:
                                pass
                        if not match:
                            s.rules[matches[0]].of_actions.append({"OUTPUT": {"action_type": "OUTPUT", "port": index}})
                    else:
                        rule = {
                            "_fl_action": "create",
                            "priority": 500,
                            "ip_src": src, "ip_dst": dst,
                            "of_actions": [{ "OUTPUT": { "action_type": "OUTPUT", "port": index }}]
                        }
                        for k,v in props.items():
                            if not isinstance(v.value, type(None)) and k in key_map.keys():
                                rule[key_map[k]] = v.value
                        s.rules.append(rule)
            result.append(s)
        result = Path(result, props)
        result.annotations = annotations
        return result
    
    result = set([])
    for e in paths:
        if e[0] == 'flow':
            assert e[2][0] == 'port' and e[-2][0] == 'port'
            src, dst = e[2][1].address.address, e[-2][1].address.address
            flow = _insert_rules(e[1:], src, dst, e.properties, e.annotations)
            result.add(flow)
        else:
            result.add(e)
    return result

def xsp_function(paths, env):
    result = set([])
    def _add_function(e, fns, neg):
        if e[0] == 'node' and fns:
            for fn in fns:
                if all([not r.function.name == fn.name for r in e[1].rules if hasattr(r, 'function')]):
                    if not hasattr(e[1], 'functions'):
                        e[1].extendSchema('functions', {})
                        e[1].functions = { "create": [], "delete": [], "active": [] }
                    s = e[1].functions
                    if neg:
                        if any([f.name == fn.name for f in s.create]):
                            raise ResolutionError("Function '{}' in transient state on '{}'".format(fn.name, e[1].name))
                        if any([f.name == fn.name for f in s.active]) and \
                           all([f.name != fn.name for f in s.delete]):
                            s.delete.append({'name': fn.name})
                    else:
                        if any([f.name == fn.name for f in s.delete]):
                            raise ResolutionError("Function '{}' in transient state on '{}'".format(fn.name, e[1].name))
                        if all([f.name != fn.name for f in list(s.active) + list(s.create)]):
                            s.create.append({'name': fn.name})
        return e[1]
    for e in paths:
        if e[0] == 'flow':
            assert e[2][0] == 'port' and e[-2][0] == 'port'
            flow = []
            for i,x in enumerate(e[1:]):
                flow.append(_add_function(x, e.annotations[i+1], e.negation))
            flow = Path(flow, e.properties, negation=e.negation)
            flow.annotations = e.annotations
            result.add(flow)
        else:
            result.add(e)
    return result
