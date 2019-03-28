import falcon
import json

from flanged.handlers.base import _BaseHandler
from flanged.handlers.utils import build_ryu_json
from flange.utils import runtime

from lace import logging

@logging.trace("flanged.query")
class QueryHandler(_BaseHandler):
    def __init__(self, conf, db, rt):
        self._log = logging.getLogger('flange.flanged')
        self.rt = runtime(rt)
        super().__init__(conf, db)

    @falcon.before(_BaseHandler.do_auth)
    @falcon.after(_BaseHandler.encode_response)
    def on_get(self, req, resp, fid):
        ir = next(self._db.find(fid, self._usr))
        ir.reset()
        try:
            netpath = ir.get_record('netpath')
            resp.body = {
                "text": ir.text,
                "netpath": netpath,
                "svg": ir.svg,
                "fid": fid,
                "ryu": build_ryu_json(json.loads(netpath[0])),
                "live": ir.live
            }
        except KeyError:
            resp.body = {}
            resp.status = falcon.HTTP_502
            return
        resp.status = falcon.HTTP_200
