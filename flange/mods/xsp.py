
def xsp_forward(path, env):
    def _insert_rules(e, src, dst):
        result = []
        for i, (ty, s) in enumerate(e):
            if ty == 'port':
                if e[i+1][0] in ['node', 'function']:
                    try:
                        rule = {
                            'ip_src': src, 'ip_dst': dst,
                            'of_actions': [
                                {'OUTPUT': {'action_type': 'OUTPUT',
                                            'port': e[i+2][1].index}}
                            ]}
                        if rule not in s.rules:
                            s.rules.append(rule)
                    except (AttributeError,IndexError):
                        pass
            result.append((ty, s))
        return result
    
    result = []
    for e in path:
        if e[0] == 'flow':
            assert e[2][0] == 'port' and e[-2][0] == 'port'
            src, dst = e[2][1].address.address, e[-2][1].address.address
            flow = ['flow']
            flow.extend(_insert_rules(e[1:], src, dst))
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
