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
    def _hash(d):
        return hash(tuple(sorted([(k,v) for k,v in d.items()])))
    def _mod_request(records, dpid, r):
        dpid, match = int(dpid), {_of_keymap[k]: v for k,v in r.items() if k in _of_keymap}
        try: del match['vlan_pcp']
        except: pass
        h = _hash(match)

        if dpid not in records: records[dpid] = record = {}
        else: record = records[dpid]

        if h in record: actions = record[h]['actions']
        else:
            record[h] = {
                'dpid': dpid,
                'priority': r.get('vlan_priority', 500),
                'match': match,
                'actions': []
            }
            actions = record[h]['actions']
        
        for v in r.get('of_actions', []):
            for d in v.values():
                d = {'type': d['action_type'], **d}
                del d['action_type']
                if d not in actions:
                    actions.append(d)

    requests = {"add": {}, "modify": {}, "delete": {}}
    for ele in npath['hops']:
        if 'ports' in ele and 'datapathid' in ele:
            for p in ele['ports']:
                actions = p.get('rule_actions', {})
                for index in actions.get('create', []):
                    _mod_request(requests['add'], ele['datapathid'], p['rules'][index])
                for index in actions.get('modify', []):
                    _mod_request(requests['modify'], ele['datapathid'], p['rules'][index])
                for index in actions.get('delete', []):
                    _mod_request(requests['delete'], ele['datapathid'], p['rules'][index])
    return requests
