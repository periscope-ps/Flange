from flange.primitives._base import fl_object

class _operation(fl_object):
    def __new__(cls, *args, **kwargs):
        obj = super().__new__(cls)
        obj.__fl_type__ = cls.__name__
        return obj
    def __fl_init__(self, operand):
        def _f(ops):
            for res in ops:
                yield res
        self.__fl_operand__ = operand
        self.__fl_query__ = _f

    def __resolve__(self):
        raise NotImplemented()
        
    def __union__(self, other):
        def _intersect(ops):
            for res in self.__resolve__():
                yield res
            for res in other.__resolve__():
                yield res
        new = exists(self.__fl_operand__)
        new.__fl_query__ = _intersect
        return new
    
    def __intersection__(self, other):
        def _union(ops):
            for r1 in self.__resolve__():
                for r2 in other.__resolve__():
                    return r1.extend(r2)
        new = exists(self.__fl_operand__)
        new.__fl_query__ = _union
        return new
        
    def __complement__(self):
        def _not(self):
            result = []
            for res in self.__resolve__():
                if len(res) == 1:
                    result.append(("delete" if res[0][0] == "create" else "create", res[0][1]))
                else:
                    result.append(("delete" if res[0][0] == "create" else "create", res))
            return result
        
        new = exists(self.__fl_operand__)
        new.__resolve__ = _f
        return new

class exists(_operation):
    def __resolve__(self):
        for res in self.__fl_query__(self.__fl_operand__.__exists__(self.__fl_operand__.__fl_members__)):
            if isinstance(res, set):
                results = []
                for r in list(res):
                    results.append(("create", r))
                yield results
            else:
                yield res
    
class forall(_operation):
    def __resolve__(self):
        result = []
        for res in self.__fl_operand__.__forall__(self.__fl_operand__.__fl_members__):
            if isinstance(res, set):
                for r in list(res):
                    result.append(("create", r))
        yield result
