import falcon
import json

from time import strftime as ftime
from time import localtime as local

from flanged.handlers.base import _BaseHandler
from flanged.handlers.utils import get_body

class SketchHandler(_BaseHandler):
    def authorize(self, grants):
        self._other = "ls" in grants
        return True
    
    @falcon.before(_BaseHandler.do_auth)
    @falcon.after(_BaseHandler.encode_response)
    def on_get(self, req, resp, usr=None):
        def _make_record(ir):
            f = "%Y-%m-%d %H:%M:%S"
            return {"created": ftime(f, local(ir.created)),
                    "modified": ftime(f, local(ir.modified)),
                    "live": ir.live}
        usr = usr or self._usr
        if not self._other and usr != self._usr:
            raise falcon.HTTPUnauthorized("User is not privilaged to view {}'s flangelets".format(usr))
        resp.body = {ir.fid: _make_record(ir) for ir in self._db.find(usr=usr)}
        resp.status = falcon.HTTP_200

