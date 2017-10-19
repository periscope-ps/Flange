import base64
import json
import os
import requests
import tornado
import tornado.httpserver

from tornado.web import url
from tornado.ioloop import IOLoop

class MainHandler(tornado.web.RequestHandler):
    def initialize(self, path):
        self.path = path
        
    def get(self, *args, **kwargs):
        self.render(self.path + "public/index.html")

class FlangeHandler(tornado.web.RequestHandler):
    def initialize(self, token):
        self.token = token
    
    def get(self, *args, **kwargs):
        r = requests.get("http://localhost:8000/")
        self.write(r.text)
        
    def post(self):
        program = self.get_argument("program", None)
        if not program:
            self.send_error(500)
        else:
            payload = { "program": program, "flags": { "type": "svg" } }
            headers = { "Authorization": "OAuth " + self.token }
            r = requests.post("http://localhost:8000/c", 
                              data=json.dumps(payload),
                              headers=headers)
            self.write(r.text[1:-1])
def main():
    # Login to server
    headers = { "Authorization": "Basic " + base64.b64encode("programmer:programmer") }
    token = requests.get("http://localhost:8000/a", headers=headers).json()["Bearer"]
    
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
    server.listen(80)
    
    IOLoop.instance().start()

if __name__ == "__main__":
    main()
