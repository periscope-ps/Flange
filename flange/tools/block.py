from flange.utils import FlangeError
from flange.tools.visitor import Visitor

import os

def ast_pprint(ast):
    _, cols = os.popen('stty size', 'r').read().split()
    cols = int(cols) - 5
    def maybe_split(v, pad):
        if len(str(v)) + len(pad) > cols and isinstance(v, Block):
            res = "{}({} ".format(pad, v.tag)
            if len(res) + len(str(v.tokens[0])) > cols:
                for t in v.tokens:
                    res += "\n" + maybe_split(t, pad + "  ")
            else:
                pad = " " * len(res)
                res += str(v.tokens[0])
                for t in v.tokens[1:]:
                    res += "\n" + maybe_split(t, pad)
            return res + ")"
        else:
            return pad + str(v)
    return maybe_split(ast, "")

class Block(Visitor):
    __slots__ = ['tokens', 'tag']
    def __init__(self, tag, tokens=None):
        tokens = tokens or []
        self.tag, self.tokens = tag, tokens

    @property
    def val(self):
        return self.tokens

    def __repr__(self):
        return ast_pprint(self)
    
    def __str__(self):
        return "("+self.tag+" "+" ".join([repr(v) for v in self.tokens])+")"
