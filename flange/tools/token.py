from flange.tools.visitor import Visitor

class Token(Visitor):
    __slots__ = ['lineno', 'charno', 'val']

    def __init__(self, val, lineno=None, charno=None):
        if isinstance(val, Token):
            self.val, self.lineno, self.charno = val.val, val.lineno, val.charno
        else:
            if isinstance(lineno, type(None)) or isinstance(charno, type(None)):
                raise TypeError("Cannot create token without line or character number")
            self.val,  self.lineno, self.charno = val, lineno, charno

    def __repr__(self):
        return self.val
    
    def __str__(self):
        return self.val
