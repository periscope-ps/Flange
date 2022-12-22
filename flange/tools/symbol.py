from flange.tools.token import Token
from flange.exceptions import FlangeSyntaxError

import re

class Symbol(Token):
    def __init__(self, val, lineno=None, charno=None):
        super().__init__(val, lineno, charno)
        valid_name = "[_A-Za-z][A-Za-z0-9_!@#$%^?*]*"
        if not re.match(valid_name, self.val):
            raise FlangeSyntaxError("invalid symbol name", self)

    def __repr__(self):
        return "(sym " + self.val + ")"

class Type(Token):
    def __repr__(self):
        return "(type " + self.val + ")"
