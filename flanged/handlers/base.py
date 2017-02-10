import base64
import bson
import falcon
import hashlib
import hmac
import json
import time

from flanged.settings import MIME

class _BaseHandler(object):
    def __init__(self, conf, db):
        self._conf = conf
        self._db = db

    @classmethod
    def do_auth(req, resp, resource, params):
        if getattr(resource._conf, 'auth', False):
            if not req.auth:
                raise falcon.HTTPMissingHeader("Authorization")
                
            bearer = req.auth.split(' ')
            if len(bearer) != 2:
                raise falcon.HTTPInvalidHeader("Malformed Authorization header")
            
            parts = req.auth.split('.')
            itok = ".".join(parts[:2])
            sig = hmac.new(resource._conf.get('secret', "there is no secret").encode('utf-8'), itok.encode('utf-8'), digestmod=hashlib.sha256).digest()
            if not hmac.compare_digest(base64.urlsafe_b64encode(sig), parts[2].encode('utf-8')):
                raise falcon.HTTPForbidden()
                
            if json.loads(parts[0])["exp"] < int(time.time()):
                raise falcon.HTTPForbidden(description="Token has expired")
                
            if not resource.authorize(json.loads(parts[1])):
                raise falcon.HTTPForbidden(description="User does not have permission to use this function")
                
            self._usr = json.loads(parts[1]["iss"])
            
    @classmethod
    def encode_response(self, req, resp, resource):
        if not req.get_header("Accept"):
            raise falcon.HTTPMissingHeader("Accept")
        
        if req.client_accepts(MIME['PSJSON']) or req.client_accepts(MIME['JSON']):
            resp.body = json.dumps(resp.body)
        elif req.client_accepts(MIME['PSBSON']) or req.client_accepts(MIME['BSON']):
            resp.body = bson.dumps(resp.body)
        
    def authorize(self, grants):
        return True
    

class SSLCheck(object):
    def __init__(self, conf):
        self._conf = conf
    
    def process_request(self, req, resp):
        if req.protocol == 'https' and self._conf.get('auth', False):
            raise falcon.HTTPBadRequest(title='400 HTTPS required', 
                                        description='Flanged requires an SSL connection to authenticate requests')
        
    def process_resource(self, req, resp, resource, params):
        pass
    def process_response(self, req, resp, resource, req_suceeded):
        pass
