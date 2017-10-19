from flange.primitives._base import fl_object

class _operation(fl_object):
    def __init__(self, operand):
        self.__fl_operand__ = operand
    
    def __fl_next__(self):
        raise NotImplemented()
        
    def __union__(self, other):
        def _intersect(ops):
            for res in self.__fl_next__():
                yield res
            for res in other.__fl_next__():
                yield res
        new = exists(None)
        new.__fl_next__ = _intersect
        return new
    
    def __intersection__(self, other):
        def _union(ops):
            for r1 in self.__fl_next__():
                for r2 in other.__fl_next__():
                    return r1 | r2
        new = exists(None)
        new.__fl_next__ = _union
        return new
    
    def __complement__(self):
        raise NotImplemented()
        #def _not(self):
        #    result = []
        #    for res in self.__resolve__():
        #        if len(res) == 1:
        #            result.append(("delete" if res[0][0] == "create" else "create", res[0][1]))
        #        else:
        #            result.append(("delete" if res[0][0] == "create" else "create", res))
        #    return result
        #
        #new = exists(self.__fl_operand__)
        #new.__resolve__ = _f
        #return new

class exists(_operation):
    def __fl_next__(self):
        for res in self.__fl_operand__.__fl_next__():
            yield res
    
class forall(_operation):
    def __fl_next__(self):
        yield set.union(*list(self.__fl_operand__.__fl_next__()))
