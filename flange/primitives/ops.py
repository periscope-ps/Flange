from flange.primitives._base import fl_object

class _operation(fl_object):
    def __init__(self, operand):
        self.__fl_operand__ = operand
    
    def __fl_next__(self):
        raise NotImplementedError()

    def __union__(self, other):
        def _f():
            for res in self.__fl_next__():
                yield res
            for res in other.__fl_next__():
                yield res
        new = _operation(None)
        new.__fl_next__ = _f
        return new
    
    def __intersection__(self, other):
        def _f():
            for r1 in self.__fl_next__():
                for r2 in other.__fl_next__():
                    yield r1 | r2
        new = _operation(None)
        new.__fl_next__ = _f
        return new
    
    def __complement__(self):
        raise NotImplementedError()

class exists(_operation):
    def __fl_next__(self):
        for res in self.__fl_operand__.__fl_next__():
            yield res
    def __complement__(self):
        def _comp(self):
            def _f():
                for v in forall.__fl_next__(self):
                    result = []
                    for r in v:
                        r.negation = True
                        result.append(r)
                    yield set(result)
            return _f
        
        result = forall(self.__fl_operand__)
        result.__fl_next__ = _comp(result)
        return result

class gather(exists):
    def __fl_next__(self):
        for res in self.__fl_operand__.__fl_gather__():
            yield res

class forall(_operation):
    def __fl_next__(self):
        yield set.union(*list(self.__fl_operand__.__fl_next__()))

    def __complement__(self):
        def _comp(self):
            def _f():
                for r in exists.__fl_next__(self):
                    r.negation = True
                    yield r

        result = exists(self.__fl_operand__)
        result.__fl_next__ = _comp(result)
        return result
