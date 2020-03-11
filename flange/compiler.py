import argparse
import json

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
from flange.backend import netpath, svg, buildchanges, waggle
from flange.exceptions import CompilerError as FlangeCompilerError
from flange.primitives import assertions

from pprint import pprint
from lace.logging import DEBUG, INFO, CRITICAL
from lace.logging import trace
from uuid import uuid4

import sys, time

passes = [findlines, tokenizer, ast, collapseflows, createobjects, rules, buildpaths]
backends = {
    "netpath": netpath,
    "svg": svg,
    "waggle": waggle
}
oldhook = sys.excepthook

class _prof(object):
    def __init__(self): self._m = []
    def start(self, n): self._m.append((n, time.time()))
    def end(self, n): self._m.append((n, time.time() - self._m.pop()[1]))
    def __repr__(self): return "<times " + " ".join(["{}:{}".format(k, v) for k,v in self._m]) + ">"

_p = _prof()

class pcode(object):
    def __init__(self, raw, frontend, env):
        self._env = env
        self._fe = frontend
        self._compiled = False
        self._changes = []
        self.created, self.modified = int(time.time()), int(time.time())
        self.text = raw
        self.live = False
        self.generated = int(time.time())
        self.fid = str(uuid4())
        self._store = {}
        self.interest = []
        self.dirty = False

    def reset(self):
        self._compiled = False

    def recompile(self):
        self._store, self._fe = {}, self.text
        for p in passes:
            self._fe = p.run(self._fe, self._env)
        self._changes, self.interest = buildchanges.run(self._fe, self._env)
        return self._changes
    
    def get_record(self, n):
        return self._store[n]

    def __getattribute__(self, n):
        if n in backends:
            if not self._compiled:
                _p.start("path")
                self._changes, self.interest = buildchanges.run(self._fe, self._env)
                _p.end("path")
                self._compiled = True
            _p.start("be")
            result = backends[n].run(self._changes, self._env)
            _p.end("be")
            self._store[n] = result
            return result
        else:
            return super().__getattribute__(n)

def get_mods(ls):
    result = []
    for p in ls:
        if isinstance(p, str):
            import importlib
            path = p.split(".")
            module = importlib.import_module(".".join(path[:-1]))
            result.append(getattr(module, path[-1]))
        else:
            result.append(p)
    return result

@trace.info("compiler")
def compile_pcode(program, loglevel=None, interactive=False, firstn=len(passes), breakpoint=None, env=None):
    raw = program
    env['mods'] = get_mods(env['mods'])
    env.setdefault('logging', loglevel)
    print("Compiling on Env: {}\n".format(env))
    if breakpoint:
        trace.setBreakpoint(breakpoint)
    
    _passes = passes[:firstn]
    for p in _passes:
        program = p.run(program, env)
        if loglevel and loglevel > 1:
            print(p.__name__)
            pprint(program)

    return pcode(raw, program, env)

@trace.info("compiler")
def flange(program, backend="netpath", loglevel=None, db=None, env=None, **kwargs):
    global _p
    try:
        _p = _prof()
        env = env or {"usr": "*"}
        env.setdefault('mods', [xsp_forward, xsp_function, xsp_tag_user])
        env.setdefault('logging', loglevel)
        assertions.LOOPCOUNT = env.setdefault('searchdepth', 1)
        utils.runtime(db)
        _p = _prof()
        _p.start("IR")
        pcode = compile_pcode(program, loglevel=loglevel, env=env)
        _p.end("IR")
        if isinstance(backend, list):
            result = {}
            for be in backend:
                result[be] = getattr(pcode, be)
            if kwargs.get('profile', None):
                print(_p)
            return result
        result = getattr(pcode, backend)
        if kwargs.get('profile', None):
            print(_p)
    except FlangeCompilerError as e:
        print("\n", e)
        exit(1)
    return result


def _passwise(program, db):
    utils.runtime(db)
    for p in passes:
        print(p.__name__)
        program = p.run(program, {})
        pprint(program)
        print()


def main():
    parser = argparse.ArgumentParser(description="Flange domain specific language compiler for network orchestartion")
    parser.add_argument('file', metavar='FILE', type=str, nargs=1,
                        help='File to compile')
    parser.add_argument('-o', '--output', type=str, default="out.d",
                        help='Output filename')
    parser.add_argument('-u', '--unis', type=str, default='http://localhost:8888')
    parser.add_argument('-v', '--verbose', type=int, default=0)
    parser.add_argument('--debugmode', action='store_true')
    parser.add_argument('-b', '--backend', type=str, nargs="*", default=['netpath'])
    parser.add_argument('-p', '--plugin', type=str, nargs="*")

    args = parser.parse_args()

    with open(args.file[0]) as f:
        program = f.read()

    env = {}
    if args.plugin:
        env['mods'] = get_mods(args.plugin)
        
    with open(args.output, 'w') as f:
        if not args.debugmode:
            f.write(json.dumps(flange(program, loglevel=args.verbose, backend=args.backend, env=env, db=args.unis), indent=2))
        else:
            json.dumps(_passwise(program, args.unis))
