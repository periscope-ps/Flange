import falcon

from flanged.handlers import CompileHandler, AuthHandler, ValidateHandler, SketchHandler, SSLCheck

# TMP Mock database object
class _Database(object):
    def __init__(self):
        self._store = {}
        self._usrs = {
            "admin": { "pwd": "admin", "prv": ["ls", "x", "v"] },
            "reader": { "pwd": "reader", "prv": ["ls"] },
            "programmer": { "pwd": "programmer", "prv": ["x"] },
            "qa": { "pwd": "qa", "prv": ["v"] }
        }
        
    ### DO NOT ACTUALLY USE THIS, IT IS horribly INSECURE ##
    def get_usr(self, usr, pwd):
        for k, v in self._usrs.items():
            if k == usr:
                if v.get("pwd", "") != pwd:
                    raise falcon.HTTPForbidden("Incorrect password")
            
                return v["prv"]
        raise falcon.HTTPForbidden("Unknown username")
        
    def find(self, usr=None):
        for k, ls in self._store.items():
            if not usr or usr == k:
                for f in ls:
                    yield f

    def insert(self, usr, flangelet):
        if usr not in self._store:
            self._store[usr] = []
        self._store[usr].append(flangelet)

def _get_app():
    conf = { "auth": True, "secret": "a4534asdfsberwregoifgjh948u12" }
    db = _Database()
    auth      = AuthHandler(conf, db)
    compiler  = CompileHandler(conf, db)
    validator = ValidateHandler(conf, db)
    sketches  = SketchHandler(conf, db)
    
    ensure_ssl = SSLCheck(conf)
    
    #app = falcon.API(middleware=[ensure_ssl])
    app = falcon.API()
    app.add_route('/c', compiler)
    app.add_route('/a', auth)
    app.add_route('/v', validator)
    app.add_route('/s', sketches)
    app.add_route('/s/{usr}', sketches)
    
    return app

def main():
    ## TODO ##
    # Self host server
    app = _get_app()
    
    from wsgiref.simple_server import make_server
    server = make_server('localhost', 8000, app)

    print("Listening on localhost:8000")
    server.serve_forever()

if __name__ == "__main__":
    main()
else:
    application = _get_app()
