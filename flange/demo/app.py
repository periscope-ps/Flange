import argparse
import base64
import json
import os
import requests
import tornado
import tornado.httpserver

from lace import logging
from lace.logging import trace
from tornado.web import url
from tornado.ioloop import IOLoop

class MainHandler(tornado.web.RequestHandler):
    @trace.info("MainHandler")
    def initialize(self, path):
        self.path = path
        
    @trace.info("MainHandler")
    def get(self, *args, **kwargs):
        self.render(self.path + "public/index.html")

class FlangeHandler(tornado.web.RequestHandler):
    @trace.info("FlangeHandler")
    def initialize(self, token, href):
        self.token = token
        self.href = href
    
    @trace.info("FlangeHandler")
    def get(self, *args, **kwargs):
        import json
        r = requests.get(self.href)
        self.write(json.dumps({ "svg": r.text }))
    
    
    @trace.info("FlangeHandler")
    def post(self):
        program = self.get_argument("program", None)
        tys = self.get_argument("type", "svg").split(",")
        if not program:
            self.send_error(500)
        else:
            payload = { "program": program, "flags": { "type":  tys } }
            headers = { "Authorization": "OAuth " + self.token }
            r = requests.post(self.href + "/c", 
                              data=json.dumps(payload),
                              headers=headers)
            self.write(r.text)
    
def main():
    parser = argparse.ArgumentParser(description="Demo application for flanged")
    parser.add_argument('-p', '--port', default='8001')
    parser.add_argument('-f', '--flanged', default='http://localhost:9001')
    args = parser.parse_args()
    
    # Login to server
    headers = { "Authorization": "Basic " + base64.b64encode("programmer:programmer".encode('utf-8')).decode('utf-8') }
    token = requests.get(args.flanged + "/a", headers=headers).json()["Bearer"]
    
    trace.setLevel(logging.DEBUG)
    ROOT = os.path.dirname(os.path.abspath(__file__)) + os.sep
    app = tornado.web.Application([url(r"/", MainHandler, { "path": ROOT }),
                                   url(r"/js/(.*)", 
                                       tornado.web.StaticFileHandler, 
                                       { "path": ROOT + "./public/js" }),
                                   url(r"/css/(.*)",
                                       tornado.web.StaticFileHandler,
                                       { "path": ROOT + "./public/css" }),
                                   url(r"/f", FlangeHandler, { "token": token,
                                                               "href": args.flanged})],
                                  autoreload = True,
                                  template_path = ROOT + "public")
    
    server = tornado.httpserver.HTTPServer(app)
    server.listen(args.port)
    
    IOLoop.instance().start()

if __name__ == "__main__":
    main()
