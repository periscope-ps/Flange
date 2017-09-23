from flange import findlines
from flange import tokenizer
from flange import ast
from flange import nodefinder
from flange import flowmaker
from flange import naiveflow
#from flange.backend import netpath

from lace.logging import DEBUG, INFO, CRITICAL
from lace.logging import trace

import sys

#passes = [findlines, tokenizer, ast, nodefinder, flowmaker, netpath]
passes = [findlines, tokenizer, ast, naiveflow]

@trace.info("Compiler")
def compile(program, loglevel=0, interactive=False):
    trace.setLevel([CRITICAL, INFO, DEBUG][loglevel], True)
    trace.runInteractive(interactive)
    
    #if not loglevel:
        #sys.excepthook = lambda extype,exp,trace: print("{}: {}".format(extype.__name__, exp))
    for p in passes:
        program = p.run(program)
        
    return program
