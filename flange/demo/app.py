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
    def initialize(self, token):
        self.token = token
    
    @trace.info("FlangeHandler")
    def get(self, *args, **kwargs):
        import json
        r = requests.get("http://localhost:8000/")
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
            r = requests.post("http://localhost:8000/c", 
                              data=json.dumps(payload),
                              headers=headers)
            self.write(r.text)
    
def main():
    # Login to server
    headers = { "Authorization": "Basic " + base64.b64encode("programmer:programmer".encode('utf-8')).decode('utf-8') }
    token = requests.get("http://localhost:8000/a", headers=headers).json()["Bearer"]
    
    trace.setLevel(logging.DEBUG)
    ROOT = os.path.dirname(os.path.abspath(__file__)) + os.sep
    app = tornado.web.Application([url(r"/", MainHandler, { "path": ROOT }),
                                   url(r"/js/(.*)", 
                                       tornado.web.StaticFileHandler, 
                                       { "path": ROOT + "./public/js" }),
                                   url(r"/css/(.*)",
                                       tornado.web.StaticFileHandler,
                                       { "path": ROOT + "./public/css" }),
                                   url(r"/f", FlangeHandler, { "token": token })],
                                  autoreload = True,
                                  template_path = ROOT + "public")
    
    server = tornado.httpserver.HTTPServer(app)
    server.listen(8001)
    
    IOLoop.instance().start()

if __name__ == "__main__":
    main()
