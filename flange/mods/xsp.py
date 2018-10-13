from flange.exceptions import ResolutionError

def xsp_forward(paths, env):
    def _find_rules(rules, src, dst, l4_src, l4_dst):
        for i,r in enumerate(rules):
            if getattr(r, 'ip_src', None) == src and getattr(r, 'ip_dst', None) == dst and \
               getattr(r, 'src_port', None) == l4_src.value and getattr(r, 'dst_port', None) == l4_dst.value:
                yield i
    
    def _insert_rules(e, src, dst, l4_src, l4_dst):
        result = []
        for i, (ty, s) in enumerate(e):
            if ty == 'port' and len(e) > i+2:
                index = e[i+2][1].index
                if e[i+1][0] in ['node', 'function']:
                    matches = list(sorted(_find_rules(s.rules, src, dst, l4_src, l4_dst), key=lambda x: getattr(s.rules[x], 'priority', 0)))
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
                                print(exp)
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
                        if not isinstance(l4_src.value, type(None)):
                            rule['src_port'] = l4_src.value
                        if not isinstance(l4_dst.value, type(None)):
                            rule['dst_port'] = l4_dst.value
                        s.rules.append(rule)
            result.append((ty, s))
        return result
    
    result = []
    for e in paths:
        if e[0] == 'flow':
            assert e[2][0] == 'port' and e[-2][0] == 'port'
            l4_src = e.properties['l4_src']
            l4_dst = e.properties['l4_dst']
            src, dst = e[2][1].address.address, e[-2][1].address.address
            flow = ['flow']
            flow.extend(_insert_rules(e[1:], src, dst, l4_src, l4_dst))
            result.append(flow)
        else:
            result.append(e)
    return result

def xsp_function(path, env):
    def _build_rule(fn):
        name, node, fn = fn
        #node.rules.append({'of_actions': [{'ATTACH_FUNCTION': {'name': name, 'fn': fn}}]})
        return (name, node, fn)
    
    result = []
    for e in path:
        pair = e
        if e[0] == 'function':
            pair = _build_rule(e[1])
        elif e[0] == 'flow':
            lres = []
            for ty, s in e[1:]:
                if ty == 'function':
                    s = _build_rule(s)
                lres.append((ty, s))
            pair = [e[0]]
            pair.extend(lres)
        result.append(pair)
    return result
