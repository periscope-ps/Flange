import base64
import json

def get_body(fn):
    def _f(self, req, resp):
        body = {}
        if req.content_length:
            body = json.loads(req.stream.read().decode('utf-8'))
        fn(self, req, resp, body)
    
    return _f

_of_keymap = {
    "src_port": "tcp_src",
    "dest_port": "tcp_dst",
    "l2_src": "eth_src",
    "l2_dst": "eth_dst",
    "vlan": "vlan_vid",
    "vlan_priority": "vlan_pcp",
    "dcsp": "ip_dscp",
    "mpls": "mpls_label",
    "mpls_class": "mpls_tc",
    "ip_src": "ipv4_src",
    "ip_dst": "ipv4_dst"
}

def build_ryu_json(npath):
    def _build_record(dpid, r):
        record = {
            'dpid': int(dpid),
            'priority': r.get('vlan_priority', 500),
            'match': {_of_keymap[k]: v for k,v in r.items() if k in _of_keymap},
            'actions': []
        }
        try: del record['match']['vlan_pcp']
        except: pass
        for v in r.get('of_actions', []):
            for d in v.values():
                d = {'type': d['action_type'], **d}
                del d['action_type']
                record['actions'].append(d)
        return record

    requests = {"add": [], "modify": []}
    for ele in npath['hops']:
        ele.setdefault('datapathid', 0) # Temporary for testing
        if 'ports' in ele and 'datapathid' in ele:
            for p in ele['ports']:
                actions = p.get('rule_actions', {})
                for index in actions.get('create', []):
                    requests['add'].append(_build_record(ele['datapathid'], p['rules'][index]))
                for index in actions.get('modify', []):
                    requests['modify'].append(_build_record(ele['datapathid'], p['rules'][index]))
    return requests

def clean_rules(rt):
    for p in rt.ports:
        remove = []
        for r in getattr(p, 'rules', []):
            action = getattr(r, '_fl_action', 'maintain')
            if action == 'delete':
                remove.append(r)
            elif action == 'create':
                r._fl_action = 'maintain'
        for r in remove:
            p.rules.remove(r)
