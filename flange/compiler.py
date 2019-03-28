import argparse
import json
import time

from flange import passes
from flange.tools.block import Block, ast_pprint
from flange.exceptions import CompilerError
from flange.types import fl_obj

def _print_exp(filename, program, exp):
    if isinstance(exp.token, Block):
        return _print_exp(filename, program, type(exp)(exp.msg, exp.token.tokens[0]))
    elif isinstance(exp.token, fl_obj):
        return _print_exp(filename, program, type(exp)(exp.msg, exp.token._toks[0]))
    line = program.split("\n")[exp.token.lineno]
    print("  [{}:{}] - {}".format(filename, exp.token.lineno, line))
    print("   {} {}    {}^".format(" " * len(filename),
                                   " " * len(str(exp.token.lineno)),
                                   " " * exp.token.charno))
    print("{} {}".format(exp.ty, exp.msg))
    

def flange(program, env=None):
    try:
        v = passes.run(program, env or [])
        return v
    except CompilerError as exp:
        _print_exp("<stdin>", program, exp)

def debug(program, env=None):
    try:
        return passes.run(program, env or [], debug=True)
    except CompilerError as exp:
        _print_exp("<stdin>", program, exp)
