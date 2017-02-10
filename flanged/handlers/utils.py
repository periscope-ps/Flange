import json

def get_body(fn):
    def _f(self, req, resp):
        body = {}
        if req.content_length:
            parts = req.stream.read().decode('utf-8')
            args = parts.split('&')
            for arg in args:
                k, v = arg.split('=')
                if v[0] in ['{', '['] and v[-1] in ['}', ']']:
                    body[k] = json.loads(v)
                else:
                    body[k] = v
        fn(self, req, resp, body)
    
    return _f
