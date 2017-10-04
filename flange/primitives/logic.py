from flange.primitives._base import fl_type
from flange.primitives.collections import fl_object

import math

class _logic(fl_object):
    def __new__(cls, *args, **kwargs):
        obj = super().__new__(cls)
        obj.__fl_type__ = cls.__name__
    def __fl_init__(self, v):
        self._v = v
    def __bool__(self):
        return bool(self._v)
    def __raw__(self):
        return self._v

class boolean(_logic):
    def __init__(self, value):
        self._v = bool(value._v)
    def __intersection__(self, other):
        return boolean(self._v and other._v)
    def __union__(self, other):
        return boolean(self._v or other._v)
    def __complement__(self):
        return not self._v

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
