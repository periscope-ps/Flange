from flange.primitives.resolvable import And, Or, Not, Exists, Forall, Gather
from flange.primitives.logic import boolean, string, number, empty
from flange.primitives.collections import fl_list
from flange.primitives.assertions import Flow, Query, Function
from flange.primitives.internal import Rule, Path, Solution
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
