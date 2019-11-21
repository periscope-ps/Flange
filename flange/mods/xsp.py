from flange.exceptions import ResolutionError
from flange.primitives.internal import Path, Solution

import logging

def xsp_forward(solution, env):
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

    def _insert_rules(e, src, dst, props, annotations, interest):
        result = []
        for i, (ty, s) in enumerate(e):
            if ty == 'port' and len(e) > i+2:
                index = None
                try: index = e[i+2][1].properties.vport_number
                except AttributeError: index = e[i+2][1].index
                if index is None:
                    logging.getLogger('flange.OF').warn("No compatible index on OF port")
                elif e[i+1][0] in ['node', 'function']:
                    interest.append(s)
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
    
    result, interest = [], []
    for path in solution.paths:
        if path[0] == 'flow':
            assert path[2][0] == 'port' and path[-2][0] == 'port'
            src, dst = path[2][1].address.address, path[-2][1].address.address
            flow = _insert_rules(path[1:], src, dst, path.properties, path.annotations, interest)
            result.append(flow)
        else:
            result.append(path)
    return Solution(result, solution.env), interest

def xsp_function(solution, env):
    result, interest = [], []
    cmp = {
        'gt': lambda a,b: a > b, 'ge': lambda a,b: a >= b,
        'lt': lambda a,b: a < b, 'le': lambda a,b: a <= b,
        'ne': lambda a,b: a != b
    }
    def _set_conf(f, conf):
        changed = False
        for k in conf.keys():
            for c,v in conf[k].items():
                if c == 'eq':
                    if getattr(f.configuration, k, float('-inf')) != v:
                        changed = True
                        setattr(f.configuration, k, v)
                elif not hasattr(f.configuration, k):
                    raise ResolutionError("Unknown function config '{}.{}'".format(f.name, k))
                elif not cmp[c](getattr(f.configuration, k), v):
                    raise ResolutionError("Invalid function config '{}.{}' {} '{}'".format(f.name, k, c, v))
        return changed
    def _add_function(e, fns, neg):
        if e[0] == 'node':
            if fns: interest.append(e[1])
            for fn in fns:
                conf = {}
                static_conf = solution.env.get(fn, {})
                for k in static_conf.keys():
                    for c,v in static_conf[k].items():
                        if c == 'eq': conf[k] = v
                if not hasattr(e[1], 'functions'):
                    e[1].extendSchema('functions', {})
                    e[1].functions = { "create": [], "delete": [], "active": [], "modified": [] }
                s = e[1].functions
                
                if neg:
                    if any([f.name == fn.name for f in s.create]):
                        raise ResolutionError("Function '{}' in transient state on '{}'".format(fn.name, e[1].name))
                    if any([f.name == fn.name for f in s.active]):
                        if all([f.name != fn.name for f in s.delete]):
                            s.delete.append({'name': fn.name, 'configuration': conf})
                        else:
                            for f in s.delete:
                                if f.name == fn.name: _set_conf(f, static_conf)
                else:
                    if any([f.name == fn.name for f in s.delete]):
                        raise ResolutionError("Function '{}' in transient state on '{}'".format(fn.name, e[1].name))
                    if all([f.name != fn.name for f in s.active]):
                        exists = False
                        for f in s.create:
                            if f.name == fn.name:
                                _set_conf(f, static_conf)
                                exists = True
                        if not exists:
                            s.create.append({'name': fn.name, 'configuration': conf})
                    else:
                        for f in s.active:
                            if f.name == fn.name and _set_conf(f, static_conf):
                                s.modified.append(f)
        return e[1]
    for path in solution.paths:
        if path[0] == 'flow':
            assert path[2][0] == 'port' and path[-2][0] == 'port'
            flow = []
            for i,x in enumerate(path[1:]):
                flow.append(_add_function(x, path.annotations[i+1], path.negation))
            flow = Path(flow, path.properties, negation=path.negation)
            flow.annotations = path.annotations
            result.append(flow)
        else:
            result.append(path)
    return Solution(result, solution.env), interest
