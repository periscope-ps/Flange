from flange.utils import runtime

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
