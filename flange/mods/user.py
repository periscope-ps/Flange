from flange.exceptions import ResolutionError
from flange.primitives.internal import Path, Solution

def filter_user(solution, env):
    def _is_valid(e):
        try:
            return env['usr'] == '*' or env['usr'] in e.users
        except AttributeError:
            return True

    interest = []
    for e in solution.paths:
        if e[0] == 'node' and _is_valid(e[1]):
            continue
        elif e[0] == 'flow' and all([_is_valid(e) for _,e in e[1:]]):
            continue
        raise ResolutionError
    return solution, []

def xsp_tag_user(solution, env):
    def _flow(e, src, dst, interest):
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
                    interest.append(s)
                    if rule not in s.rules:
                        s.rules.append(rule)
            res.append(s)
        res = Path(res, e.properties)
        res.annotations = e.annotations
        return res
    
    if env['usr'] in ['*', 'admin']:
        return solution

    result, interest = [], []
    for e in solution.paths:
        if e[0] == 'flow':
            assert e[2][0] == 'port' and e[-2][0] == 'port'
            src, dst = e[2][1].address.address, e[-2][1].address.address
            result.append(_flow(e[1:], src, dst, interest))
        else:
            result.append(e)

    return Solution(result, solution.env), interest
