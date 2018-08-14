import argparse
import falcon
import json

from flanged.handlers import CompileHandler, AuthHandler, ValidateHandler, SketchHandler, GraphHandler, SSLCheck
from unis import Runtime
from unis.services.graph import UnisGrapher
from unis.services.graphbuilder import Graph

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
        
    ### DO NOT ACTUALLY USE THIS, IT IS horribly INSECURE ###
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

def _build_graph(rt, size, push):
    rt.nodes.createIndex('name')
    g = Graph.power_graph(size, 1, db=rt)
    if push:
        g.finalize()

def _get_app(unis, layout, size=None, push=False):
    conf = { "auth": True, "secret": "a4534asdfsberwregoifgjh948u12" }
    db = _Database()
    rt = Runtime(unis, proxy={'defer_update': True})
    rt.addService(UnisGrapher)
    if size:
        _build_graph(rt, size, push)
    else:
        rt.nodes.load()
        rt.links.load()
    
    if not layout or not rt.graph.load(layout):
        rt.graph.spring(30)
        rt.graph.dump('layout.json')
    
    auth      = AuthHandler(conf, db)
    compiler  = CompileHandler(conf, db, rt)
    validator = ValidateHandler(conf, db, rt)
    sketches  = SketchHandler(conf, db)
    graph     = GraphHandler(conf, db, rt)
    #subscribe = SubscriptionHandler(conf)
    
    ensure_ssl = SSLCheck(conf)
    
    #app = falcon.API(middleware=[ensure_ssl])
    app = falcon.API()
    app.add_route('/', graph)
    app.add_route('/c', compiler)
    app.add_route('/a', auth)
    app.add_route('/v', validator)
    app.add_route('/l', sketches)
    app.add_route('/l/{usr}', sketches)
    #app.add_route('/s', subscribe)
    
    return app
    
def main():
    from lace import logging
    parser = argparse.ArgumentParser(description='flanged provides a RESTful server for the processing and maintainance of flangelets.')
    parser.add_argument('-u', '--unis', default='http://localhost:8888', type=str, help='Set the comma diliminated urls to the unis instances of interest')
    parser.add_argument('-p', '--port', default=8000, type=int, help='Set the port for the server')
    parser.add_argument('-d', '--debug', default=0, type=int, help='Set the log level')
    parser.add_argument('-s', '--size', default=0, type=int, help='Use a demo graph of the given size')
    parser.add_argument('-p', '--push', action='store_true', help='When used with --size, pushes the generated graph to the back end data store for future use')
    parser.add_argument('--layout', default='', help='Set the default SVG layout for the topology')
    args = parser.parse_args()
    
    logging.trace.setLevel([logging.NOTSET, logging.INFO, logging.DEBUG][args.debug])
    port = args.port
    layout = args.layout
    unis = [str(u) for u in args.unis.split(',')]
    app = _get_app(unis, layout, args.size, args.push)
    
    from wsgiref.simple_server import make_server
    server = make_server('localhost', port, app)
    port = "" if port == 80 else port
    print("Getting topology from {}".format(unis))
    print("Listening on {}{}{}".format('http://localhost',":" if port else "", port))
    server.serve_forever()
    
if __name__ == "__main__":
    main()
