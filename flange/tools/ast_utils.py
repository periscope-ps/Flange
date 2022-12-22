from flange.tools import fl_lift
from flange.tools.block import Block
from flange.tools.token import Token
from flange.tools.symbol import Symbol, Type
from flange.exceptions import FlangeSyntaxError

class SkipInstance(Exception): pass

class match(object):
    def __init__(self, state):
        self._next = state
    def __call__(self, tokens):
        tokens = tokens.tokens if isinstance(tokens, Block) else tokens
        blk = Block(self._next, tokens)
        return blk

class exact(match):
    ty_lut = {
        "sym": Symbol,
        "type": Type,
        "tok": fl_lift
    }
    def __call__(self, tokens):
        if len(tokens) != 1:
            raise SkipInstance()

        if callable(self._next):
            if not isinstance(tokens[0], Block):
                raise SkipInstance()
            return self._next(tokens[0])
        else:
            if not isinstance(tokens[0], Token):
                raise SkipInstance()
            return self.ty_lut[self._next](tokens[0])
