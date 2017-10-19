from flange.primitives._base import fl_type
from flange.primitives.collections import fl_object

import math

class _logic(fl_object):
    def __init__(self, v):
        self._v = v
    def __eq__(self, other):
        if isinstance(other, fl_object):
            return boolean(self._v == other._v)
        else:
            return boolean(False)
    def __ne__(self, other):
        if isinstance(other, fl_object):
            return boolean(self._v != other._v)
        else:
            return boolean(False)
    def __gt__(self, other):
        if isinstance(other, fl_object):
            return boolean(self._v > other._v)
        else:
            return boolean(False)
    def __ge__(self, other):
        if isinstance(other, fl_object):
            return boolean(self._v <= other._v)
        else:
            return boolean(False)
    def __lt__(self, other):
        if isinstance(other, fl_object):
            return boolean(self._v < other._v)
        else:
            return boolean(False)
    def __le__(self, other):
        if isinstance(other, fl_object):
            return boolean(self._v <= other._v)
        else:
            return boolean(False)
    def __bool__(self):
        return bool(self._v)
    def __raw__(self):
        return self._v
    def __repr__(self):
        return "<{} {}>".format(self.__fl_type__, self._v)

class boolean(_logic):
    def __init__(self, value):
        if isinstance(value, fl_object):
            self._v = bool(value._v)
        else:
            self._v = bool(value)
    def __intersection__(self, other):
        return boolean(self._v and other._v)
    def __union__(self, other):
        return boolean(self._v or other._v)
    def __complement__(self):
        return boolean(not self._v)

class number(_logic):
    def __add__(self, other):
        return number(self._v + other._v)
    def __sub__(self, other):
        return number(self._v - other._v)
    def __mult__(self, other):
        return number(self._v * other._v)
    def __div__(self, other):
        return number(self._v / other._v)
    def __mod__(self, other):
        return number(self._v % other._v)
    def __intersection__(self, other):
        return boolean(self).__intersection__(boolean(other))
    def __union__(self, other):
        return boolean(self).__union__(boolean(other))
    def __complement__(self):
        return boolean(self).__complement__()
    
class string(_logic):
    def __add__(self, other):
        self.__union__(other)
    def __mult__(self, other):
        return string(self._v * other._v)
    def __div__(self, other):
        if not isinstance(other, number):
            raise TypeError("Cannot divide string by {}".format(other.__fl_type__))
        _l = math.ceil(len(self._v) / other._v)
        
        return fl_list([string(self._v[s:s + _l]) for s in range(0, len(self._v), _l)])
    def __union__(self, other):
        return string("{}{}".format(self._v, self._v))
    def __intersection__(self, other):
        raise NotImplemented()
    def __complement__(self):
        raise NotImplemented()

class empty(_logic):
    def __eq__(self, other):
        if isinstance(other, empty):
            return boolean(True)
        return boolean(False)
    def __gt__(self, other):
        raise NotImplemented()
    def __lt__(self, other):
        raise NotImplemented()
