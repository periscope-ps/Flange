from flange.exceptions import ResolutionError


def filter_user(path, env):
    def _is_valid(e):
        try:
            return env['usr'] == '*' or env['usr'] in e.users
        except AttributeError:
            return True

    for e in path:
        if e[0] == 'node' and _is_valid(e[1]):
            continue
        elif e[0] == 'flow' and all([_is_valid(e) for _,e in e[1:]]):
            continue
        raise ResolutionError
    return path

def xsp_tag_user(path, env):
    def _flow(e, src, dst):
        res, tag = [], False
        for i, (ty, s) in enumerate(e):
            if not tag:
                if ty == 'port' and e[i+1][0] in ['node', 'function']:
                    tag = True
                    rule = {
                        '_fl_action': "create",
                        'ip_src': src, 'ip_dst': dst,
                        'of_actions': [
                            {'SET_FIELD': {'action_type': 'SET_FIELD',
                                           'field': 'ip_dscp',
                                           'value': 16}}
                        ]}
                    if rule not in s.rules:
                        s.rules.append(rule)
            res.append((ty, s))
        return res
    
    if env['usr'] in ['*', 'admin']:
        return path

    result = []
    for e in path:
        if e[0] == 'flow':
            assert e[2][0] == 'port' and e[-2][0] == 'port'
            src, dst = e[2][1].address.address, e[-2][1].address.address
            ls = [e[0]]
            ls.extend(_flow(e[1:], src, dst))
            result.append(ls)
        else:
            result.append(e)
        
    return result
