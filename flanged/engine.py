import threading, time

from unis.services import RuntimeService
from unis.services.event import new_event, update_event

def run(db, rt):
    def _thread():
        while True:
            for ir in db.find():
                if ir.dirty:
                    print(" {} is dirty, evaluating".format(ir.fid))
                    ir.reset()
                    result = ir.recompile()
                    print(ir.waggle)
                    rt.flush()
                    ir.dirty = False
            time.sleep(1)

    threading.Thread(None, _thread, 'flanged.engine', daemon=True).start()

class Service(RuntimeService):
    def __init__(self, db):
        self.db = db

    @new_event(['nodes', 'ports', 'links'])
    def register_new(self, resource):
        for ir in self.db.find():
            if not ir.dirty:
                ir.dirty = True
    @update_event(['nodes', 'ports', 'links'])
    def check_solutions(self, resource):
        for ir in self.db.find():
            if not ir.dirty and resource in ir.interest:
                ir.dirty = True
