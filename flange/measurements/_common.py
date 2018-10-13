from flange.utils import runtime
from flange.primitives._base import fl_object
from flange.exceptions import CompilerError

from functools import reduce
from unis.measurements import Last

def Builder(prop, f, default):
    def func(path):
        pnames = [n[1].name for n in path if n[0] == 'node']
        subjects = [i for i in range(1, len(path)) if path[i][0] == 'link']
        md = [runtime().metadata.first_where({'subject': path[s][1], 'eventType': prop}) for s in subjects]
        measures = []
        ids = []
        for m in md:
            if m and not hasattr(m.data, 'last'):
                m.data.attachFunction(Last())
            measures.append(m.data.last if m else default)
            ids.append(m.id if m else None)
        result = reduce(lambda x,y: f([x,y]), measures)
        return result
    
    return func

def StaticBuilder(prop, f, default):
    def func(path):
        links = [path[i][1] for i in range(1, len(path)) if path[i][0] == 'link']
        return reduce(lambda x,y: f([x,y]), [getattr(l, prop, default) for l in links])
    return func


class _flange_prop(fl_object):
    def __init__(self, name):
        self.name = name
        self._value = None

    @property
    def value(self):
        if isinstance(self._value, type(None)):
            return None
        return self._value.__raw__()
    
    def __eq__(self, other):
        self._value = other
        return True
        
def PropertyBuilder(name):
    def func(path):
        prop = _flange_prop(name)
        path.properties[name] = prop
        return prop
    return func
