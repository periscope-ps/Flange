from flange.exceptions import FlangeSyntaxError
from flange.tools import fl_str
from flange.tools.block import Block

from collections import namedtuple

"""
Pass 2: Group

Takes the :class:`Tokens <flange.tools.token.Token>` from pass 1 and builds groups out of lists
and paren'd groups of :class:`Tokens <flange.tools.token.Token>`.

"""

def _dequote(toks):
    result, i = [], 0
    while i < len(toks):
        if toks[i].val in ['"', "'"]:
            _, i = result.append(fl_str(toks[i+1])), i + 3
        else:
            _, i = result.append(toks[i]), i + 1
    return result

def _collapse_parens(toks, depth=0):
    result = []
    while toks:
        head = toks.pop(0)
        if head.val == ")":
            if depth == 0:
                raise FlangeSyntaxError("Unmmatched parenthesis", head)
            return Block("(", result), toks
        else:
            if head.val == "(":
                head, toks = _collapse_parens(toks, depth+1)
            result.append(head)
    return Block("program", result), []

def run(program, env):
    return _collapse_parens(_dequote(program))[0]
