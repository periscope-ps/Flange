import falcon
import json

from flanged.handlers.base import _BaseHandler
from flanged.handlers.utils import get_body

class SketchHandler(_BaseHandler):
    def __init__(self, conf, db):
        super(SketchHandler, self).__init__(conf, db)
        self._other = True
    
    @falcon.before(_BaseHandler.do_auth)
    @falcon.after(_BaseHandler.encode_response)
    def on_get(self, req, resp, usr=None):
        query = None
        if not self._other:
            if usr != self._usr:
                raise falcon.HTTPUnauthorized("User is not privilaged to view other users flangelets")
            query = self._db.find(self._usr)
        elif usr:
            query = self._db.find(body["usr"])
        else:
            query = self._db.find()
        
        result = []
        for f in query:
            result.append(f)
        resp.body = result
        resp.status = falcon.HTTP_200
    
    def authorize(self, payload):
        self._other = True if "ls" in payload["prv"].split(',') else False
        return True
    
