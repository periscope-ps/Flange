from flange.primitives._base import fl_object

class fl_list(fl_object):
    def __init__(self, ls):
        self._ls = ls
    
    def __getitem__(self, index):
        return self._ls[index]
        
    def __setitem__(self, index, value):
        self._ls[index] = value
    
    def append(self, value):
        self._ls.append(value)
    
    def __union__(self, other):
        if isinstance(other, fl_list):
            return fl_list(self._ls + other._ls)
        else:
            return fl_list(self._ls + [other])
    def __intersection__(self, other):
        if isinstance(other, fl_list):
            return fl_list([x for x in self._ls if x in other._ls])
        else:
            return fl_list([other]) if other in self._ls else fl_list([])
    def __complement__(self):
        raise NotImplemented()
    def __bool__(self):
        return bool(self._ls)
    def __raw__(self):
        return self._ls
    def __eq__(self, other):
        if isinstance(other, fl_list):
            return super().__eq__(other)
        else:
            return other in self._ls
    def __iter__(self, other):
        for x in self._ls:
            yield x
