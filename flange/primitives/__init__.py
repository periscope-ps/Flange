from flange.primitives.resolvables import query, flow, function
from flange.primitives.logic import boolean, string, number, empty
from flange.primitives.collections import fl_list
from flange.primitives.ops import exists, forall, gather
from flange.primitives.internal import Rule, Path
from flange.primitives import _base

from lace.logging import trace

@trace.debug("types")
def lift_type(arg):
    if isinstance(arg, _base.fl_object):
        return arg
    if isinstance(arg, str):
        return string(arg)
    elif isinstance(arg, (int, float)):
        return number(arg)
    elif isinstance(arg, bool):
        return boolean(arg)
    elif isinstance(arg, type(None)):
        return empty(arg)
    elif hasattr(arg, '__iter__'):
        return fl_list([lift_type(x) for x in arg])
    else:
        raise ValueError("Unknown type in compiler - {}".format(arg))
