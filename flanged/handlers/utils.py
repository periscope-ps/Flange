import base64
import json

def get_body(fn):
    def _f(self, req, resp):
        body = {}
        if req.content_length:
            body = json.loads(req.stream.read().decode('utf-8'))
        fn(self, req, resp, body)
    
    return _f

def build_ryu_json(npath):
    requests = {"add": [], "modify": []}
    for ele in npath['hops']:
        if 'ports' in ele and 'datapathid' in ele:
            for p in ele['ports']:
                if 'rules' in p:
                    for r in p['rules']:
                        action = r.get("_fl_action", "maintain")
                        of_actions = []
                        for v in r['of_actions']:
                            for d in v.values():
                                if 'port' in d:
                                    d['port'] = int(d['port'])
                                if 'action_type' in d:
                                    d['type'] = d['action_type']
                                    del d['action_type']
                                of_actions.append(d)
                        record = {
                            'dpid': int(ele['datapathid']),
                            'priority': r.get('priority', 500),
                            'match': {'ipv4_src': r['ip_src'],
                                      'ipv4_dst': r['ip_dst'],
                                      'eth_type': 2048},
                            'actions': of_actions
                        }
                        if "src_port" in r:
                            record['match']['tcp_src'] = r['src_port']
                            record['match']['ip_proto'] = 6
                        if "dst_port" in r:
                            record['match']['tcp_dst'] = r['dst_port']
                            record['match']['ip_proto'] = 6
                        if action == "create":
                            requests['add'].append(record)
                        elif action == "modify":
                            requests['modify'].append(record)
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
