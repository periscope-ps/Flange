import base64
import falcon
import hashlib
import hmac
import json
import time

from flanged import settings
from flanged.handlers.base import _BaseHandler
from flanged.handlers.utils import get_body


class AuthHandler(_BaseHandler):
    @falcon.after(_BaseHandler.encode_response)
    @get_body
    def on_post(self, req, resp, body):
        try:
            token = req.get_header('Authorization')
            up = base64.b64decode(token.split('Basic ')[1]).decode('utf-8')
            (user, passwd) = up.split(':')
        except:
            raise falcon.HTTPInvalidHeader("Could not perform HTTP-BASIC Auth", "Authorization")
            
        header = { "alg": "HS256", "typ": "JWT" }
        payload = { 
            "iss": user, 
            "exp": int(time.time()) + settings.TOKEN_TTL,
            "prv": ",".join(self._db.get_usr(user, passwd))
        }
        tok = self._generate_token(header, payload)
        
        resp.body = { "Bearer": tok }
        resp.status = falcon.HTTP_200
        
    def _generate_token(self, header, payload):
        b_header = base64.urlsafe_b64encode(json.dumps(header).encode('utf-8'))
        b_payload = base64.urlsafe_b64encode(json.dumps(payload).encode('utf-8'))
        itok = ".".join([b_header.decode('utf-8'), b_payload.decode('utf-8')])
        sig = hmac.new(self._conf.get('secret', "there is no secret").encode('utf-8'), itok.encode('utf-8'), digestmod=hashlib.sha256).digest()
        return ".".join([itok, base64.urlsafe_b64encode(sig).decode('utf-8')])
