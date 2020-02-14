import falcon
import json
from lace import logging
from unis.models import Flow

from flange import compiler
from flange.mods.user import filter_user, xsp_tag_user
from flange.mods.openflow import openflow_mod
from flange.utils import reset_rules, runtime

from flanged.handlers.base import _BaseHandler
from flanged.handlers.utils import get_body, build_ryu_json

class CompileHandler(_BaseHandler):
    def __init__(self, conf, db, rt):
        self._log = logging.getLogger('flange.flanged')
        self.rt = runtime(rt)
        super().__init__(conf, db)

    @falcon.before(_BaseHandler.do_auth)
    @falcon.after(_BaseHandler.encode_response)
    @get_body
    def on_post(self, req, resp, body):
        #reset_rules.reset(self.rt)
        if "program" not in body:
            raise falcon.HTTPInvalidParam("Compilation request requires a program field", "program")
        flags = body.get("flags", {})
        ty = flags.get("type", "netpath")
        mods = flags.get("mods", [])
        tys = ty if isinstance(ty, list) else [ty]
        print(tys, mods)
        try:
            ir = self.compute(body["program"], tys, mods)
        except falcon.HTTPUnprocessableEntity as exp:
            resp.body = { "error": str(exp) }
            resp.status = falcon.HTTP_500
            return

        self._db.insert(self._usr, ir)

        delta, do_ryu = {'ryu': {'add': {}, 'modify': {}, 'delete': {}}}, False
        if 'netpath' not in tys: delta['netpath'] = {}
        if 'ryu' in tys:
            do_ryu = True
            tys.remove('ryu')
        for ty in tys:
            delta[ty] = getattr(ir, ty)
        delta['fid'] = ir.fid
        if do_ryu:
            for path in delta['netpath']:
                try:
                    v = build_ryu_json(json.loads(path))
                    delta['ryu']['add'].update(v['add'])
                    delta['ryu']['modify'].update(v['modify'])
                    delta['ryu']['delete'].update(v['delete'])
                except Exception as e:
                    self._log.error("Graph missing critical attributes for generating 'netpath' - {}".format(e))
        else: delta['ryu'] = {}

        self.rt.flush()
        resp.body = delta
        resp.status = falcon.HTTP_200

    def authorize(self, attrs):
        return True if "x" in attrs else False
        
    def compute(self, prog, ty="netpath", mods=None):
        try:
            env = {'usr': self._usr, 'mods': mods or [openflow_mod]}
            result = compiler.compile_pcode(prog, 1, env=env)
            
        except Exception as exp:
            import traceback
            traceback.print_exc()
            raise falcon.HTTPUnprocessableEntity(exp)
        
        return result
