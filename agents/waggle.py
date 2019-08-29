from unis import Runtime
from unis.services import RuntimeService
from unis.services.event import new_update_event

import argparse, time

class Service(RuntimeService):
    def _start(self, fn, node):
        print("Starting '{}' on '{}' with\n  {}".format(fn.name, node.name, fn.configuration.to_JSON(top=False)))
    def _stop(self, fn, node):
        print("Stopping '{}' on '{}'".format(fn.name, node.name))

    def initialize(self):
        for n in self.runtime.nodes:
            self._check_update(n)
        self.runtime.flush()

    def _check_update(self, node):
        updated = False
        if hasattr(node, 'functions'):
            if not hasattr(node.functions, 'active'):
                node.functions.active = []
            if hasattr(node.functions, 'create') and node.functions.create:
                updated, todo = True, []
                for fn in node.functions.create:
                    self._start(fn, node)
                    todo.append(fn)
                for fn in todo:
                    node.functions.create.remove(fn)
                    node.functions.active.append(fn)
            if hasattr(node.functions, 'delete') and node.functions.delete:
                updated, delete, active = True, [], []
                for fn in node.functions.delete:
                    self._stop(fn, node)
                    for f in node.functions.active:
                        if f.name == fn.name:
                            active.append(f)
                    delete.append(fn)
                [node.functions.active.remove(f) for f in active]
                [node.functions.delete.remove(f) for f in delete]
            if hasattr(node.functions, 'modified') and node.functions.modified:
                updated, todo = True, []
                for fn in node.functions.modified:
                    self._stop(fn, node)
                    self._start(fn, node)
                    todo.append(fn)
                [node.functions.modified.remove(fn) for fn in todo]
        if updated:
            self.runtime._update(node)
        
    @new_update_event('nodes')
    def maintain_plugins(self, node):
        self._check_update(node)

def main(unis):
    rt = Runtime(unis)
    rt.addService(Service)
    
    while True:
        time.sleep(1)
        rt.flush()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--unis', type=str)
    args = parser.parse_args()
    
    main(args.unis)
