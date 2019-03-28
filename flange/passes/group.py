from flange.exceptions import FlangeSyntaxError
from flange.tools.block import Block
from flange.types import fl_str

from collections import namedtuple

"""
Pass 2: Group

Takes the :class:`Tokens <flange.tools.token.Token>` from pass 1 and builds groups out of lists
and paren'd groups of :class:`Tokens <flange.tools.token.Token>`.



"""

_match = namedtuple("_match", ["ty", "val", "recur"])
_match.__new__.__defaults__ = (True,)
str_builder = lambda _,v: fl_str(v[0])
def _build_block(toks, start=None, recur=True):
    pairs = {'"': _match(str_builder, '"', False),
             "'": _match(str_builder, "'", False),
             "(": _match(Block, ")")}
    result, i = [], 0
    while i < len(toks):
        if toks[i].val in pairs.keys() and recur:
            tok, j = _build_block(toks[i+1:], toks[i], pairs[toks[i].val].recur)
            i += j+1
        else:
            if not start and toks[i].val in [v.val for v in pairs.values()]:
                if start == "(":
                    raise FlangeSyntaxError("Unmatched parenthesis", toks[i])
                if start in ["'", '"']:
                    raise FlangeSyntaxError("Reached EOF before closing string", toks[i])
            tok, i = toks[i], i+1
        if start and tok.val == pairs[start.val].val:
            return pairs[start.val].ty("group", result), i
        result.append(tok)
    if start:
        raise FlangeSyntaxError("Unmatched parenthesis", start)
    return Block("program", result), i

def run(program, env):
    return _build_block(program)[0]
