import argparse
import json
import time

from flange import utils
from flange import findlines
from flange import tokenizer
from flange import ast
from flange import collapseflows
from flange import rules
from flange import createobjects
from flange import buildpaths
from flange.mods.xsp import xsp_forward, xsp_function
from flange.mods.user import filter_user, xsp_tag_user
from flange.backend import netpath, svg, buildchanges

from lace.logging import DEBUG, INFO, CRITICAL
from lace.logging import trace
from uuid import uuid4

import sys

passes = [findlines, tokenizer, ast, collapseflows, createobjects, rules, buildpaths]
backends = {
    "netpath": netpath,
    "svg": svg
}
oldhook = sys.excepthook

class pcode(object):
    def __init__(self, raw, frontend, env):
        self._env = env
        self._fe = frontend
        self._compiled = False
        self._changes, self._rejected = [], []
        self.created, self.modified = int(time.time()), int(time.time())
        self.text = raw
        self.live = False
        self.generated = int(time.time())
        self.fid = str(uuid4())
        self._store = {}


    def reset(self):
        self._compiled = False

    def get_record(self, n):
        return self._store[n]

    def __getattribute__(self, n):
        if n in backends:
            if not self._compiled:
                self._changes, self._rejected = buildchanges.run(self._fe, self._env)
                self._compiled = True
            result = backends[n].run(self._changes, self._env)
            self._store[n] = result
            return result
        else:
            return super().__getattribute__(n)

@trace.info("compiler")
def compile_pcode(program, loglevel=None, interactive=False, firstn=len(passes), breakpoint=None, env=None):
    raw = program
    print("Compiling on Env: {}".format(env))
    if loglevel:
        trace.setLevel([CRITICAL, INFO, DEBUG][min(loglevel, 2)], True, showreturn=(loglevel > 2))
        trace.runInteractive(interactive)
    if breakpoint:
        trace.setBreakpoint(breakpoint)
    
    _passes = passes[:firstn]
    for p in _passes:
        program = p.run(program, env)

    return pcode(raw, program, env)
    

@trace.info("compiler")
def flange(program, backend="netpath", loglevel=None, db=None, env=None):
    env = env or {"usr": "*"}
    if 'mods' not in env:
        env['mods'] = []
    env['mods'].extend([xsp_forward, xsp_function, xsp_tag_user])
    utils.runtime(db)
    pcode = compile_pcode(program, loglevel=loglevel, env=env)
    if isinstance(backend, list):
        result = {}
        for be in backend:
            result[be] = getattr(pcode, be)
        return result
    return getattr(pcode, backend)


def _passwise(program, db):
    from pprint import pprint
    utils.runtime(db)
    for p in passes:
        print(p.__name__)
        program = p.run(program, {})
        pprint(program)
        print()


def main():
    parser = argparse.ArgumentParser(description="DLT File Transfer Tool")
    parser.add_argument('file', metavar='FILE', type=str, nargs=1,
                        help='File to compile')
    parser.add_argument('-o', '--output', type=str, default="out.d",
                        help='Output filename')
    parser.add_argument('-u', '--unis', type=str, default='http://localhost:8888')
    parser.add_argument('-v', '--verbose', type=int, default=0)
    parser.add_argument('--debugmode', action='store_true')



    args = parser.parse_args()
    
    with open(args.file[0]) as f:
        program = f.read()
        
    with open(args.output, 'w') as f:
        if not args.debugmode:
            f.write(json.dumps(flange(program, loglevel=args.verbose, db=args.unis)))
        else:
            json.dumps(_passwise(program, args.unis))
