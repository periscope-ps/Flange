import falcon, json, time, requests

from flanged.handlers.base import _BaseHandler
from flanged.handlers.utils import build_ryu_json
from flange.utils import runtime

from lace import logging
from pprint import pprint
from threading import Thread, Lock, Event
from requests.exceptions import ConnectionError

class InsertError(Exception): pass

class PushFlowHandler(_BaseHandler):
    def __init__(self, conf, db, rt):
        self._log = logging.getLogger('flange.flanged')
        self.rt = runtime(rt)
        super().__init__(conf, db)

    def _push_to_controller(self, mods):
        if (mods['add'] or mods['modify']) and self._conf['controller']:
            print()
            print("New Flow Rules: {}".format(self._conf['controller']))
            print("  Adding Flows:")
            for add in mods['add']:
                try:
                    pprint(add)
                    r = requests.post("{}/stats/flowentry/add".format(self._conf['controller']), data=json.dumps(add))
                    print(r.status_code)
                except ConnectionError as exp:
                    raise InsertError()
            print("  Modifying Flows:")
            for modify in mods['modify']:
                try:
                    pprint(modify)
                    requests.post("{}/stats/flowentry/modify".format(self._conf['controller']), data=json.dumps(modify))
                    print(r.status_code)
                except ConnectionError:
                    raise InsertError()
            print()

    def _track_flangelet(self, ir):
        while True:
            mods = {'add': [], 'modify': []}
            ir.reset()
            for path in ir.netpath:
                path = json.loads(path)
                v = build_ryu_json(path)
                mods['add'].extend(v['add'])
                mods['modify'].extend(v['modify'])
            try:
                self._push_to_controller(mods)
                for path in ir.netpath:
                    path = json.loads(path)
                    for ele in path['hops']:
                        if 'ports' in ele:
                            for port in ele['ports']:
                                if 'rule_actions' in port:
                                    port = rt.ports.first_where({'id': port['id']})
                                    port.rule_actions.add = []
                                    port.rule_actions.modify = []
            except InsertError: pass
            time.sleep(5)

    def authorize(self, grants):
        self._other = "ls" in grants
        self.tracking = 0
        return True
    
    @falcon.before(_BaseHandler.do_auth)
    @falcon.after(_BaseHandler.encode_response)
    def on_post(self, req, resp, fid):
        self.tracking += 1
        ir = next(self._db.find(fid, self._usr))
        #mods = build_ryu_json(json.loads(ir.get_record('netpath')[0]))
        #self._push_to_ryu(mods)
        ir.live = True

        runner = Thread(target=self._track_flangelet, name="live_flangelet_{}".format(self.tracking), args=(ir,), daemon=True)
        runner.start()

    @falcon.before(_BaseHandler.do_auth)
    def on_delete(self, req, resp, fid):
        self.tracking -= 1
        if not self._db.remove(self._usr, self._db.find(fid, self._usr)):
            resp.status = falcon.HTTP_404
        else:
            resp.status = falcon.HTTP_200
