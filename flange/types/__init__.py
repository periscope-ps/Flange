from flange.tools.symbol import Symbol, Type
from flange.tools.token import Token
import re

def fl_lift(v):
    if isinstance(v, (fl_obj, fl_type)):
        return v
    elif isinstance(v, Type):
        return fl_type(v)
    elif v.val.isdigit():
        v.val = int(v.val)
        return fl_num(v)
    elif re.match("\d+(\.\d+)?", v.val) or re.match("\.\d+", v.val):
        v.val = float(v.val)
        return fl_num(v)
    elif v.val in ["True", "False"]:
        v.val = v.val == "True"
        return fl_bool(v)
    elif v.val == "None":
        v.val = None
        return fl_empty(v)
    else:
        return Symbol(v)


class fl_type(Type):
    def __call__(self, v):
        return fl_lift(v)
class fl_obj(Token):
    tag = "<badtag>"
    def __repr__(self):
        return "({} {})".format(self.tag, self.val)

class fl_str(fl_obj):
    tag = "str"
class fl_num(fl_obj):
    tag = "num"
class fl_bool(fl_obj):
    tag = "bool"
class fl_empty(fl_obj):
    tag = "empty"
