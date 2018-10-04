import falcon
import json
from lace import logging
from unis.models import Flow

from flange import compiler
from flange.mods.user import filter_user, xsp_tag_user

from flanged.handlers.base import _BaseHandler
from flanged.handlers.utils import get_body

class CompileHandler(_BaseHandler):
    def __init__(self, conf, db, rt):
        self._log = logging.getLogger('flange.flanged')
        self.rt = rt
        super().__init__(conf, db)
    
    @falcon.before(_BaseHandler.do_auth)
    @falcon.after(_BaseHandler.encode_response)
    @get_body
    def on_post(self, req, resp, body):
        if "program" not in body:
            raise falcon.HTTPInvalidParam("Compilation request requires a program field", "program")
        ty = body.get("flags", {}).get("type", "netpath")
        ty = ty if isinstance(ty, list) else [ty]
        if "netpath" not in ty:
            ty.append("netpath")
        try:
            delta = self.compute(body["program"], ty)
        except falcon.HTTPUnprocessableEntity as exp:
            resp.body = { "error": str(exp) }
            resp.status = falcon.HTTP_500
            return

        delta['ryu'] = self.build_ryu_json(json.loads(delta['netpath'][0]))
        resp.body = delta
        resp.status = falcon.HTTP_200
        
    def authorize(self, attrs):
        return True if "x" in attrs else False
        
    def compute(self, prog, ty="netpath"):
        try:
            env = {'usr': self._usr}
            result = compiler.flange(prog, ty, 1, self.rt, env=env)
            
            from flange.utils import reset_rules
            reset_rules.reset(self.rt)
            
        except Exception as exp:
            import traceback
            traceback.print_exc()
            raise falcon.HTTPUnprocessableEntity(exp)
        
        self.rt.flush()
        self._db.insert(self._usr, prog)
        return result


    def build_ryu_json(self, npath):
        requests = []
        for ele in npath['hops']:
            if 'ports' in ele and 'datapathid' in ele:
                for p in ele['ports']:
                    if 'rules' in p:
                        for r in p['rules']:
                            requests.append({
                                'dpid': int(ele['datapathid']),
                                'priority': 500,
                                'match': {'nw_src': r['ip_src'],
                                          'nw_dst': r['ip_src']},
                                'action': r['of_actions']
                            })
        return requests
        
