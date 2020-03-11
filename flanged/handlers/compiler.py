import falcon, json, time
from lace import logging
from unis.models import Flow

from flange import compiler
from flange.mods.user import filter_user, xsp_tag_user
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
    def on_put(self, req, resp, body, fid=None):
        if fid is None:
            resp.body = { "error": "Cannot PUT without flangelet ID" }
            resp.status = falcon.HTTP_404
            return

        try: ir = next(self._db.find(fid, self._usr))
        except StopIteration:
            resp.body = { "error": "Unknown flangelet ID" }
            resp.status = falcon.HTTP_404
            return
        old_ts = ir.created
        if not self._db.remove(self._usr, ir):
            resp.body = { "error": "Unknown flanglet ID" }
            resp.status = falcon.HTTP_404
            return
        
        try: ir, tys = self._compile(body)
        except falcon.HTTPUnprocessableEntity as exp:
            resp.body = { "error": str(exp) }
            resp.status = falcon.HTTP_500
            return
        ir.fid = str(fid)
        ir.created, ir.modified = old_ts, int(time.time())
        resp.body = self._build_result(ir, tys)
        resp.status = falcon.HTTP_200
        
    @falcon.before(_BaseHandler.do_auth)
    @falcon.after(_BaseHandler.encode_response)
    @get_body
    def on_post(self, req, resp, body, fid=None):
        if fid is not None:
            resp.body = { "error": "Cannot POST to specific flangelet, use PUT instead" }
            resp.status = falcon.HTTP_405
            resp.append_header("Allow", "PUT")
            return
        try: ir, tys = self._compile(body)
        except falcon.HTTPUnprocessableEntity as exp:
            resp.body = { "error": str(exp) }
            resp.status = falcon.HTTP_500
            return

        resp.body = self._build_result(ir, tys)
        resp.status = falcon.HTTP_200

    def authorize(self, attrs):
        return True if "x" in attrs else False
        
    def compute(self, prog, ty="netpath", mods=None):
        try:
            env = {'usr': self._usr, 'mods': mod, 'searchdepth': 1}
            result = compiler.compile_pcode(prog, 1, env=env)

        except Exception as exp:
            import traceback
            traceback.print_exc()
            raise falcon.HTTPUnprocessableEntity(exp)

        return result

    def _compile(self, body):
        if "program" not in body:
            raise falcon.HTTPInvalidParam("Compilation request requires a program field", "program")
        flags = body.get("flags", {})
        ty = flags.get("type", "netpath")
        mods = flags.get("mods", [])
        tys = ty if isinstance(ty, list) else [ty]
        print(tys, mods)
        return self.compute(body["program"], tys, mods), tys

    def _build_result(self, ir, tys):
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
        return delta
