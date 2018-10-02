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
            resp.body = self.compute(body["program"], ty)
            resp.status = falcon.HTTP_200
        except falcon.HTTPUnprocessableEntity as exp:
            resp.body = { "error": str(exp) }
            resp.status = falcon.HTTP_500
        
    def authorize(self, attrs):
        return True if "x" in attrs else False
        
    def compute(self, prog, ty="netpath"):
        try:
            env = {'usr': self._usr}
            result = compiler.flange(prog, ty, 1, self.rt, env=env)
            
            from flange.utils import reset_rules
            reset_rules.reset()
            #links = []
            #for path in result["netpath"]:
            #    path = json.loads(path)
            #    for hop in path["hops"]:
            #        if "directed" in hop:
            #            links.append({'rel': 'full', 'href': hop["selfRef"]})
            #    
            #    flow = Flow({"hops": links})
            #    flow.validate()
            #    print(flow)
            #    print(self.rt._pending)
            #    self.rt.insert(Flow({ "hops": links }), commit=True)
            
        except Exception as exp:
            import traceback
            traceback.print_exc()
            raise falcon.HTTPUnprocessableEntity(exp)
        
        self.rt.flush()
        self._db.insert(self._usr, prog)
        return result
