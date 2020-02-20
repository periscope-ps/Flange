import argparse, copy, falcon, json, lace, logging
import unis as unislib
from configparser import ConfigParser
from collections import defaultdict
from unis.services.graph import UnisGrapher
from unis.services.graphbuilder import Graph

from flanged import handlers
from flanged import engine
from flanged.settings import DEFAULT_CONFIG

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
        
    def find(self, fid=None, usr=None):
        for k, ls in self._store.items():
            if not usr or usr == k:
                for f in ls:
                    if not fid or f.fid == fid:
                        yield f

    def insert(self, usr, flangelet):
        if usr not in self._store:
            self._store[usr] = []
        self._store[usr].append(flangelet)

    def remove(self, usr, flangelet):
        if isinstance(flangelet, (int, str)):
            try: flangelet = next(self.find(str(flangelet), usr))
            except StopIteration: return False
        if usr not in self._store:
            return False
        self._store[usr].remove(flangelet)
        return True

def _build_graph(rt, size, push):
    rt.nodes.createIndex('name')
    g = Graph.power_graph(size, 1, db=rt)
    if push:
        g.finalize()

def _get_app(unis, layout, size=None, push=False, controller=None, community=None):
    log = logging.getLogger('flanged')
    conf = { "auth": True, "secret": "a4534asdfsberwregoifgjh948u12", "controller": controller, 'community': community }
    db = _Database()
    if not unis:
        if not community:
            log.error("Invalid configuration: needs at least one UNIS instance or a community")
        rt = unislib.from_community(community)
    else:
        rt = unislib.Runtime(unis, proxy={'defer_update': True})
    rt.addService(UnisGrapher)
    rt.addService(engine.Service(db))
    engine.run(db, rt)
    
    if size:
        _build_graph(rt, size, push)
    else:
        rt.nodes.load()
        rt.links.load()
    
    if not layout or not rt.graph.load(layout):
        rt.graph.spring(30)
        rt.graph.dump('layout.json')
    
    auth      = handlers.AuthHandler(conf, db)
    compiler  = handlers.CompileHandler(conf, db, rt)
    validator = handlers.ValidateHandler(conf, db, rt)
    sketches  = handlers.SketchHandler(conf, db)
    graph     = handlers.GraphHandler(conf, db, rt)
    query     = handlers.QueryHandler(conf, db, rt)
    push      = handlers.PushFlowHandler(conf, db, rt)
    
    ensure_ssl = handlers.SSLCheck(conf)
    
    #app = falcon.API(middleware=[ensure_ssl])
    app = falcon.API()
    app.add_route('/', graph)
    app.add_route('/c', compiler)
    app.add_route('/c/{fid}', compiler)
    app.add_route('/a', auth)
    app.add_route('/v', validator)
    app.add_route('/l', sketches)
    app.add_route('/l/{usr}', sketches)
    app.add_route('/q/{fid}', query)
    app.add_route('/p/{fid}', push)
    
    return app

def _read_config(file_path):
    if not file_path:
        return copy.copy(DEFAULT_CONFIG)
    parser = ConfigParser(allow_no_value=True)
    
    try:
        parser.read(file_path)
    except Exception:
        raise AttributeError("INVALID FILE PATH FOR STATIC RESOURCE INI.")
        return

    config = parser['CONFIG']
    try:
        return {'unis': json.loads(str(config.get('unis', DEFAULT_CONFIG['unis']))),
                'debug': int(config.get('debug', DEFAULT_CONFIG['debug'])),
                'port': int(config.get('port', DEFAULT_CONFIG['port'])),
                'layout': config.get('layout', DEFAULT_CONFIG['layout']),
                'ryu_controller': config.get('ryu-controller', DEFAULT_CONFIG['ryu_controller']),
                'community': config.get('community', DEFAULT_CONFIG['community']),
                'size': config.get('size', DEFAULT_CONFIG['size'])}
    except Exception as e:
        print(e)
        raise AttributeError('Error in config file, please ensure file is '
                             'formatted correctly and contains values needed.')
    
    
def main():
    parser = argparse.ArgumentParser(description='flanged provides a RESTful '
                                     'server for the processing and '
                                     'maintainance of flangelets.')
    parser.add_argument('-u', '--unis', type=str, help='Set the comma '
                        'diliminated urls to the unis instances of interest')
    parser.add_argument('-p', '--port', type=int, help='Set the port for the '
                        'server')
    parser.add_argument('-d', '--debug', type=int, help='Set the log level')
    parser.add_argument('-s', '--size', type=int, help='Use a demo graph of '
                        'the given size')
    parser.add_argument('-f', '--push', action='store_true', help='When used '
                        'with --size, pushes the generated graph to the back '
                        'end data store for future use')
    parser.add_argument('--layout', help='Set the default SVG layout for the '
                        'topology')
    parser.add_argument('-r', '--ryu-controller', type=str, help='Set the url'
                        ' to the ryu controller used to configure the network')
    parser.add_argument('-C', '--community', type=str, help='Set the community '
                        'name for the network community.')
    parser.add_argument('-c', '--config', type=str, help='Start flanged using '
                        'paremeters defined from a conf file. ex) flanged -c '
                        '/your/path/to/file.ini')
    args = parser.parse_args()
    
    def serve(port, app):
        from wsgiref.simple_server import make_server
        server = make_server('0.0.0.0', port, app)
        port = "" if port == 80 else port
        log = logging.getLogger('flange.flanged')
        log.info("Listening on port {}".format(port))
        server.serve_forever()

    conf = _read_config(args.config)
    conf.update(**{k:v for k,v in args.__dict__.items() if v is not None})
    print(conf)
    if isinstance(conf['unis'], str):
        conf['unis'] = [str(u) for u in conf['unis'].split(',')]

    log = logging.getLogger('flange.flanged')
    if conf['debug']:
        levels = [lace.logging.NOTSET, lace.logging.INFO, lace.logging.DEBUG, lace.logging.TRACE_OBJECTS,
                  lace.logging.TRACE_PUBLIC, lace.logging.TRACE_ALL]
        logging.basicConfig(format='%(color)s[%(asctime)-15s] [%(levelname)s] %(name)s%(reset)s %(message)s')
        #stdout = logging.StreamHandler()
        #stdout.setFormatter(logging.Formatter("{color}[{levelname} {asctime} {name}]{reset} {message}", style="{"))
        log.setLevel(levels[min(conf['debug'], 5)])
        #log.addHandler(stdout)

    log.info("Configuration:")
    for k,v in conf.items():
        log.info("{:>14}: {}".format(k, v))
    log.info("Reading topology from {}...".format(conf['unis'] or conf['community']))
    app = _get_app(conf['unis'], conf['layout'], conf['size'], conf['push'], conf['ryu_controller'], conf['community'])
    serve(conf['port'], app)

if __name__ == "__main__":
    main()
