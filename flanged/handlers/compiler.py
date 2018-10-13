import falcon
import json
from lace import logging
from unis.models import Flow

from flange import compiler
from flange.mods.user import filter_user, xsp_tag_user
from flange.mods.xsp import xsp_forward
from flange.utils import reset_rules, runtime

from flanged.handlers.base import _BaseHandler
from flanged.handlers.utils import get_body, build_ryu_json, clean_rules

class CompileHandler(_BaseHandler):
    def __init__(self, conf, db, rt):
        self._log = logging.getLogger('flange.flanged')
        self.rt = runtime(rt)
        super().__init__(conf, db)

    @falcon.before(_BaseHandler.do_auth)
    @falcon.after(_BaseHandler.encode_response)
    @get_body
    def on_post(self, req, resp, body):
        reset_rules.reset(self.rt)
        if "program" not in body:
            raise falcon.HTTPInvalidParam("Compilation request requires a program field", "program")
        ty = body.get("flags", {}).get("type", "netpath")
        tys = ty if isinstance(ty, list) else [ty]
        if "netpath" not in tys:
            tys.append("netpath")
        try:
            ir = self.compute(body["program"], ty)
        except falcon.HTTPUnprocessableEntity as exp:
            resp.body = { "error": str(exp) }
            resp.status = falcon.HTTP_500
            return

        self._db.insert(self._usr, ir)

        delta = {}
        for ty in tys:
            delta[ty] = getattr(ir, ty)
        delta['fid'] = ir.fid
        delta['ryu'] = build_ryu_json(json.loads(delta['netpath'][0]))
        
        resp.body = delta
        resp.status = falcon.HTTP_200
        
    def authorize(self, attrs):
        return True if "x" in attrs else False
        
    def compute(self, prog, ty="netpath"):
        try:
            env = {'usr': self._usr, 'mods': [xsp_forward]}
            result = compiler.compile_pcode(prog, 1, env=env)
            
        except Exception as exp:
            import traceback
            traceback.print_exc()
            raise falcon.HTTPUnprocessableEntity(exp)
        
        return result        
