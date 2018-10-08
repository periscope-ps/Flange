import argparse, os, time
import base64, json
import requests, tornado, tornado.httpserver

from lace import logging
from lace.logging import trace
from tornado.web import url
from tornado.ioloop import IOLoop

def authenticate(href):
    headers = { "Authorization": "Basic " + base64.b64encode("admin:admin".encode('utf-8')).decode('utf-8') }
    t = requests.get(href + "/a", headers=headers).json()["Bearer"]
    p = t.split('.')
    if len(p) != 3:
        raise falcon.HTTPUnauthorized("Token is not a valid JWT token")
    return t, json.loads(base64.urlsafe_b64decode(p[1]).decode('utf-8'))['exp']

            
class MainHandler(tornado.web.RequestHandler):
    @trace.info("MainHandler")
    def initialize(self, path):
        self.path = path
        
    @trace.info("MainHandler")
    def get(self, *args, **kwargs):
        self.render(self.path + "public/index.html")


class ListHandler(tornado.web.RequestHandler):
    @trace.info("ListHandler")
    def initialize(self, href):
        self.href = href

    @trace.info("ListHandler")
    def get(self, *args, **kwargs):
        headers = {"Authorization": "OAuth " + self.application.check_ttl(self.href)}
        r = requests.get(self.href + "/l", headers=headers)
        if r.status_code >= 400:
            self.write("Error from the server[{}]".format(r.status_code))
        else:
            self.write(r.text)

class PushHandler(tornado.web.RequestHandler):
    @trace.info("ListHandler")
    def initialize(self, href):
        self.href = href

    @trace.info("PushHandler")
    def post(self, fid):
        headers = {"Authorization": "OAuth " + self.application.check_ttl(self.href)}
        
        r = requests.post(self.href + "/p/" + fid, headers=headers)
        if r.status_code >= 400:
            self.write("Error from server - [{}]".format(r.status_code))
        
            
class QueryHandler(tornado.web.RequestHandler):
    @trace.info("QueryHandler")
    def initialize(self, href):
        self.href = href

    @trace.info("QueryHandler")
    def get(self, uid):
        headers = {"Authorization": "OAuth " + self.application.check_ttl(self.href)}
        
        r = requests.get(self.href + "/q/" + uid, headers=headers)
        if r.status_code >= 400:
            self.write("Error from server - [{}]".format(r.status_code))
        else:
            self.write(r.text)

class FlangeHandler(tornado.web.RequestHandler):
    @trace.info("FlangeHandler")
    def initialize(self, href):
        self.href = href
    
    @trace.info("FlangeHandler")
    def get(self, *args, **kwargs):
        import json
        r = requests.get(self.href)
        self.write(json.dumps({ "svg": r.text }))
    
    
    @trace.info("FlangeHandler")
    def post(self):
        headers = {"Authorization": "OAuth " + self.application.check_ttl(self.href)}

        program = self.get_argument("program", None)
        tys = self.get_argument("type", "svg").split(",")
        if not program:
            self.send_error(500)
        else:
            payload = { "program": program, "flags": { "type":  tys } }
            r = requests.post(self.href + "/c",
                              data=json.dumps(payload),
                              headers=headers)
            if r.status_code >= 400:
                self.write("Error from server - [{}]".format(r.status_code))
            else:
                self.write(r.text)

class Flanged(tornado.web.Application):
    def initialize(self):
        self.ttl, self.token = 0, ''
    
    def check_ttl(self, href):
        if self.ttl < int(time.time()):
            self.token, self.ttl = authenticate(href)
        return self.token
        
                
def main():
    parser = argparse.ArgumentParser(description="Demo application for flanged")
    parser.add_argument('-p', '--port', default='8001')
    parser.add_argument('-f', '--flanged', default='http://localhost:9001')
    args = parser.parse_args()
    
    trace.setLevel(logging.DEBUG)
    ROOT = os.path.dirname(os.path.abspath(__file__)) + os.sep
    app = Flanged([url(r"/", MainHandler, { "path": ROOT }),
                   url(r"/js/(.*)", 
                       tornado.web.StaticFileHandler, 
                       { "path": ROOT + "./public/js" }),
                   url(r"/css/(.*)",
                       tornado.web.StaticFileHandler,
                       { "path": ROOT + "./public/css" }),
                   url(r"/f", FlangeHandler,
                       {"href": args.flanged}),
                   url(r"/l", ListHandler, {"href": args.flanged }),
                   url(r"/q/([^/]+)", QueryHandler, {"href": args.flanged }),
                   url(r"/p/([^/]+)", PushHandler, {"href": args.flanged })],
                  autoreload = True,
                  template_path = ROOT + "public")

    app.initialize()
    server = tornado.httpserver.HTTPServer(app)
    server.listen(args.port)
    
    IOLoop.instance().start()

if __name__ == "__main__":
    main()
