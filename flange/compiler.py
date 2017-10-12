import argparse
import json

from flange import findlines
from flange import tokenizer
from flange import ast
from flange import collapseflows
from flange import createobjects
from flange import buildpaths
from flange.backend import netpath

from lace.logging import DEBUG, INFO, CRITICAL
from lace.logging import trace

import sys

passes = [findlines, tokenizer, ast, collapseflows, createobjects, buildpaths, netpath]
oldhook = sys.excepthook

@trace.info("Compiler")
def flange(program, loglevel=0, interactive=False, firstn=len(passes), breakpoint=None):
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
        
    return json.dumps(program)


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
