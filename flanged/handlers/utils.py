import json

def get_body(fn):
    def _f(self, req, resp):
        body = {}
        if req.content_length:
            jstr = req.stream.read().decode('utf-8')
            body = json.loads(jstr)
        fn(self, req, resp, body)
    return _f
