import falcon

from flange import compiler

from flanged.handlers.base import _BaseHandler
from flanged.handlers.utils import get_body

class CompileHandler(_BaseHandler):
    @falcon.before(_BaseHandler.do_auth)
    @falcon.after(_BaseHandler.encode_response)
    @get_body
    def on_post(self, req, resp, body):
        if "program" not in body:
            raise falcon.HTTPInvalidParam("Compilation request requires a program field", "program")
        if "flags" in body:
            # Optional compiler flags
            pass
        
        resp.body = self.compute(body["program"])
        resp.status = falcon.HTTP_200

    def authorize(self, attrs):
        return True if "x" in attrs else False
        
    def compute(self, prog):
        try:
            result = compiler.flange(prog)
        except Exception as exp:
            raise falcon.HTTPUnprocessableEntity(exp)
            
        self._db.insert(self._usr, prog)
        return tmpResult
