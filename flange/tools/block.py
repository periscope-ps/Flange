from __future__ import annotations
from flange import tools

import os, json
from dataclasses import dataclass, field

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

@dataclass(slots=True)
class Block(object):
    tag: str
    tokens: list[Token | Block] = field(default_factory=list)
    @property
    def val(self):
        return self.tokens

    def serialize(self):
        return {"tokens": [t.serialize() for t in self.tokens], "tag": self.tag}
    @classmethod
    def deserialize(cls, data):
        if isinstance(data, str): data = json.loads(data)
        if "tag" in data:
            return cls(data["tag"], [Block.deserialize(t) for t in data["tokens"]])
        else:
            return tools.types[data["tokentype"]].deserialize(data)
    
    def __repr__(self):
        return ast_pprint(self)
    
    def __str__(self):
        return "("+self.tag+" "+" ".join([repr(v) for v in self.tokens])+")"
