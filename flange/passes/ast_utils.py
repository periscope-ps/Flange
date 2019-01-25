from flange.tools.block import Block
from flange.tools.token import Token
from flange.tools.symbol import Symbol, Type
from flange.types import fl_lift
from flange.exceptions import FlangeSyntaxError

class SkipInstance(Exception): pass

class match(object):
    def __init__(self, state):
        self._next = state
    def __call__(self, tokens):
        tokens = tokens.tokens if isinstance(tokens, Block) else tokens
        blk = Block(self._next, tokens)
        blk.state = self._next
        return blk

class exact(match):
    ty_lut = {
        "sym": Symbol,
        "type": Type,
        "tok": lambda x: x
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
            return fl_lift(self.ty_lut[self._next](tokens[0]))
    
"""
class match(object):
    def __init__(self, value):
        self.value = value
        self.include = callable(value) or isinstance(self.value, type)
    def __call__(self, tag, v):
        if isinstance(self.value, type):
            return v[0]
        elif callable(self.value):
            return self.value("", v)
        return v
    def chk(self, v):
        if isinstance(self.value, type):
            return isinstance(v, self.value)
        if callable(self.value):
            try:
                return self.value("", v)
            except FlangeSyntaxError:
                return False
        else:
            return self.value == v.val

def maybe_block(t,v):
    return Block(t,v) if len(v) > 1 else v[0]
def symbol_block(t,v):
    return Block(t,v) if len(v) > 1 else symbol(t,v)
def symbol(t,items):
    items = items if isinstance(items, list) else [items]
    if len(items) > 1:
        raise FlangeSyntaxError("token must be symbol", items[0])
    return Symbol(items[0])
def sym_type(t,items):
    items = items if isinstance(items, list) else [items]
    if len(items) > 1:
        raise FlangeSyntaxError("Bad type name")
    return Type(items[0])
"""
