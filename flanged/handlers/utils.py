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
    requests = {"add": [], "remove": []}
    for ele in npath['hops']:
        if 'ports' in ele and 'datapathid' in ele:
            for p in ele['ports']:
                if 'rules' in p:
                    for r in p['rules']:
                        action = r.get("_fl_action", "maintain")
                        record = {
                            'dpid': int(ele['datapathid']),
                            'priority': r.get('priority', 500),
                            'match': {'nw_src': r['ip_src'],
                                      'nw_dst': r['ip_dst']},
                            'action': r['of_actions']
                        }
                        if "src_port" in r:
                            record['tp_src'] = r['src_port']
                        if "dest_port" in r:
                            record['tp_dst'] = r['dest_port']
                        if action == "create":
                            requests['add'].append(record)
                        elif action == "delete":
                            requests['remove'].append(record)
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
