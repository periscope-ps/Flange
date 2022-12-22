from __future__ import annotations
import sys, json
from dataclasses import dataclass
from typing import Union

@dataclass(slots=True)
class Token(object):
    lineno: int
    charno: int
    val: Union[Token, str]

    def __init__(self, val, lineno=None, charno=None):
        if isinstance(val, Token):
            self.val, self.lineno, self.charno = val.val, val.lineno, val.charno
        else:
            if isinstance(lineno, type(None)) or isinstance(charno, type(None)):
                raise TypeError("Cannot create token without line or character number")
            self.val,  self.lineno, self.charno = val, lineno, charno

    def serialize(self):
        return {"value": self.val, "lineno": self.lineno, "charno": self.charno,
                "tokentype": self.__class__.__name__}
    @classmethod
    def deserialize(cls, data):
        if isinstance(data, str): data = json.loads(data)
        return cls(data["value"], data["lineno"], data["charno"])

    def __repr__(self):
        return self.val
    
    def __str__(self):
        return self.val
