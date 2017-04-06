import falcon

from flanged.handlers.base import _BaseHandler
from flanged.handlers.utils import get_body

class ValidateHandler(_BaseHandler):
    @falcon.before(_BaseHandler.do_auth)
    @falcon.after(_BaseHandler.encode_response)
    @get_body
    def on_post(self, req, resp, body):
        if "changes" not in body:
            raise falcon.HTTPInvalidParam("Compilation request requires a changes field", "changes")
        
        resp.body = self.validate(body["changes"])
        resp.status = falcon.HTTP_200

    def authorize(self, attrs):
        return True if "v" in attrs else False

    def validate(self, graph):
        #TODO:
        #  Generate graph from source and "graph"
        #  attempt to run current sketches against new graph
        #  return resulting errors
        return {}
