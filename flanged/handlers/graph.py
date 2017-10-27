import falcon

from flanged.handlers.base import _BaseHandler
from flanged.handlers.utils import get_body

class GraphHandler(_BaseHandler):
    def __init__(self, conf, db, rt):
        self.rt = rt
        super().__init__(conf, db)
    
    #@falcon.before(_BaseHandler.do_auth)
    @get_body
    def on_get(self, req, resp, body):
        resp.body = str(self.rt.graph.svg())
        resp.content_type = falcon.MEDIA_HTML
        resp.status = falcon.HTTP_200
