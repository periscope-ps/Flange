import argparse
import json

from flange import utils
from flange import findlines
from flange import tokenizer
from flange import ast
from flange import collapseflows
from flange import createobjects
from flange import buildpaths
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
    def __init__(self, frontend):
        self._fe = frontend
        
    def __getattribute__(self, n):
        if n in backends:
            return backends[n].run(self._fe)
        else:
            return super().__getattribute__(n)

@trace.info("compiler")
def compile_pcode(program, loglevel=None, interactive=False, firstn=len(passes), breakpoint=None):
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
        program = p.run(program)
        
    return pcode(program)
    

@trace.info("compiler")
def flange(program, backend="netpath", loglevel=None, db=None):
    utils.runtime(db)
    pcode = compile_pcode(program, loglevel)
    if isinstance(backend, list):
        result = {}
        for be in backend:
            result[be] = getattr(pcode, be)
        return result
    return getattr(pcode, backend)




def main():
    parser = argparse.ArgumentParser(description="DLT File Transfer Tool")
    parser.add_argument('file', metavar='FILE', type=str, nargs=1,
                        help='File to compile')
    parser.add_argument('-o', '--output', type=str, default="out.d",
                        help='Output filename')



    args = parser.parse_args()
    
    with open(args.file[0]) as f:
        program = f.read()
        
    with open(args.output, 'w') as f:
        f.write(flange(program))
