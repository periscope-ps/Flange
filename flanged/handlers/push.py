import falcon, json, time, requests

from flanged.handlers.base import _BaseHandler
from flanged.handlers.utils import build_ryu_json, clean_rules
from flange.utils import runtime

from lace import logging
from pprint import pprint
from threading import Thread, Lock, Event
from requests.exceptions import ConnectionError

class PushFlowHandler(_BaseHandler):
    def __init__(self, conf, db, rt):
        self._log = logging.getLogger('flange.flanged')
        self.rt = runtime(rt)
        super().__init__(conf, db)

    def _track_flangelet(self, ir):
        print(self._conf)
        while True:
            ir.reset()
            mods = build_ryu_json(json.loads(ir.netpath[0]))
            try:
                clean_rules(self.rt)
            except Exception as exp:
                print(exp)
            if mods['add'] or mods['remove']:
                print()
                print("New Flow Rules: {}".format(self._conf['controller']))
                print("  Adding Flows:")
                for add in mods['add']:
                    try:
                        pprint(add)
                        requests.post("{}/stats/flowentry/add".format(self._conf['controller']), data=json.dumps(add))
                    except ConnectionError:
                        pass
                print("  Removing Flows:")
                for remove in mods['remove']:
                    try:
                        pprint(remove)
                        requests.post("{}/stats/flowentry/delete".format(self._conf['controller']), data=json.dumps(remove))
                    except ConnectionError:
                        pass
                print()
            time.sleep(1)
            
    
    def authorize(self, grants):
        self._other = "ls" in grants
        self.tracking = 0
        return True
    
    @falcon.before(_BaseHandler.do_auth)
    @falcon.after(_BaseHandler.encode_response)
    def on_post(self, req, resp, fid):
        self.tracking += 1
        ir = next(self._db.find(fid, self._usr))
        ir.live = True

        runner = Thread(target=self._track_flangelet, name="live_flangelet_{}".format(self.tracking), args=(ir,), daemon=True)
        runner.start()
