import argparse
import json

from flange import utils
from flange import findlines
from flange import tokenizer
from flange import ast
from flange import collapseflows
from flange import createobjects
from flange import buildpaths
from flange.mods.xsp import xsp_forward, xsp_function
from flange.mods.user import filter_user, xsp_tag_user
from flange.backend import netpath, svg

from lace.logging import DEBUG, INFO, CRITICAL
from lace.logging import trace

import sys

passes = [findlines, tokenizer, ast, collapseflows, createobjects, buildpaths]
backends = {
    "netpath": netpath,
    "svg": svg
}
oldhook = sys.excepthook

class pcode(object):
    def __init__(self, frontend, env):
        self._env = env
        self._fe = frontend
        
    def __getattribute__(self, n):
        if n in backends:
            return backends[n].run(self._fe, self._env)
        else:
            return super().__getattribute__(n)

@trace.info("compiler")
def compile_pcode(program, loglevel=None, interactive=False, firstn=len(passes), breakpoint=None, env=None):
    if loglevel:
        trace.setLevel([CRITICAL, INFO, DEBUG][min(loglevel, 2)], True, showreturn=(loglevel > 2))
        trace.runInteractive(interactive)
    if breakpoint:
        trace.setBreakpoint(breakpoint)
    
    if not loglevel:
        sys.excepthook = lambda extype,exp,trace: print("{}: {}".format(extype.__name__, exp))
    else:
        sys.excepthook = oldhook
    _passes = passes[:firstn]
    for p in _passes:
        program = p.run(program, env)

    return pcode(program, env)
    

@trace.info("compiler")
def flange(program, backend="netpath", loglevel=None, db=None, env=None):
    env = env or {"usr": "*"}
    if 'mods' not in env:
        env['mods'] = []
    env['mods'].extend([filter_user, xsp_forward, xsp_function])
    utils.runtime(db)
    pcode = compile_pcode(program, loglevel=loglevel, env=env)
    if isinstance(backend, list):
        result = {}
        for be in backend:
            result[be] = getattr(pcode, be, env)
        return result
    return getattr(pcode, backend, env)




def main():
    parser = argparse.ArgumentParser(description="DLT File Transfer Tool")
    parser.add_argument('file', metavar='FILE', type=str, nargs=1,
                        help='File to compile')
    parser.add_argument('-o', '--output', type=str, default="out.d",
                        help='Output filename')
    parser.add_argument('-u', '--unis', type=str, default='http://localhost:8888')



    args = parser.parse_args()
    
    with open(args.file[0]) as f:
        program = f.read()
        
    with open(args.output, 'w') as f:
        f.write(json.dumps(flange(program, db=args.unis)))
