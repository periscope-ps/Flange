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
        if (mods['add'] or mods['modify'] or mods['delete']) and self._conf['controller']:
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
                    r = requests.post("{}/stats/flowentry/modify".format(self._conf['controller']), data=json.dumps(modify))
                    print(r.status_code)
                except ConnectionError:
                    raise InsertError()
            print("  Deleting Flows:")
            for delete in mods['delete']:
                try:
                    pprint(delete)
                    r = requests.post("{}/stats/flowentry/delete".format(self._conf['controller']), data=json.dumps(delete))
                    print(r.status_code)
                except ConnectionError:
                    raise InsertError()
            print()

    def _track_flangelet(self, fid):
        while True:
            try: ir = next(self._db.find(fid, self._usr))
            except StopIteration: return

            ir.live = True
            mods = {'add': [], 'modify': [], 'delete': []}
            ir.reset()
            for path in ir.netpath:
                path = json.loads(path)
                v = build_ryu_json(path)
                for _,rules in v['add'].items():
                    mods['add'].extend(rules.values())
                for _,rules in v['modify'].items():
                    mods['modify'].extend(rules.values())
                for _,rules in v['delete'].items():
                    mods['delete'].extend(rules.values())
            try:
                self._push_to_controller(mods)
                for path in ir.netpath:
                    path = json.loads(path)
                    for ele in path['hops']:
                        if 'ports' in ele:
                            for port in ele['ports']:
                                if 'rule_actions' in port:
                                    port = self.rt.ports.first_where({'id': port['id']})
                                    for rule in reversed(sorted(port.rule_actions.delete)):
                                        port.rules.remove(port.rules[rule])
                                    port.rule_actions.create = []
                                    port.rule_actions.modify = []
                                    port.rule_actions.delete = []
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
        try:
            if not next(self._db.find(fid, self._usr)).live:
                runner = Thread(target=self._track_flangelet, name="live_flangelet_{}".format(self.tracking), args=(fid,), daemon=True)
                runner.start()
        except StopIteration:
            pass

    @falcon.before(_BaseHandler.do_auth)
    def on_delete(self, req, resp, fid):
        self.tracking -= 1
        if not self._db.remove(self._usr, self._db.find(fid, self._usr)):
            resp.status = falcon.HTTP_404
        else:
            resp.status = falcon.HTTP_200
