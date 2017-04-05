import falcon

from flanged.handlers.base import _BaseHandler
from flanged.handlers.utils import get_body

tmpResult = {
    "$schema": "unis.crest.iu.edu/schema/20160630/topology#",
    "id": "example-delta-graph",
    "nodes": 
    [
        {
            "id": "example-node1",
            "selfRef": "http://unis.crest.iu.edu:8888/nodes/example-node1",
            "rules": 
            [
                { 
                    "action": "create",
                    "object": 
                    {
                        "$schema": "unis.crest.iu.edu/schema/20160630/link#",
                        "id": "new-link",
                        "directed": True,
                        "endpoints": 
                        {
                            "source": {
                                "href": "http://unis.crest.iu.edu:8888/nodes/example-node1",
                                "rel": "full"
                            },
                            "sink": {
                                "href": "http://unis.crest.iu.edu:8888/nodes/example-node2",
                                "rel": "full"
                            }
                        },
                        "vlan": 340,
                    }
                },
                {
                    "action": "modify",
                    "object": 
                    {
                        "$schema": "unis.crest.iu.edu/schema/20160630/link#",
                        "id": "old-link",
                        "selfRef": "http://unis.crest.iu.edu:8888/links/old-link#",
                        "directed": False,
                        "endpoints": [ "http://unis.crest.iu.edu:8888/nodes/example-node1", "http://unis.crest.iu.edu:8888/nodes/example-node2" ],
                        "vlan": 341
                    }
                }
            ]
        }
    ]
}

class CompileHandler(_BaseHandler):
    @falcon.before(_BaseHandler.do_auth)
    @falcon.after(_BaseHandler.encode_response)
    @get_body
    def on_post(self, req, resp, body):
        if "program" not in body:
            raise falcon.HTTPInvalidParam("program", "Compilation request requires a program field")
        
        if "flags" in body:
            # Optional compiler flags
            pass
        
        resp.body = self.compute(body["program"])
        resp.status = falcon.HTTP_200

    def authorize(self, payload):
        return True if "x" in payload["prv"].split(',') else False
        
    def compute(self, prog):
        #TODO: CALL FLANGE HERE
        syntaxError = False
        if syntaxError:
            raise falcon.HTTPUnprocessableEntity(syntaxError)
            
        self._db.insert(self._usr, prog)
        return tmpResult
