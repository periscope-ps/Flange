from flange.primitives._base import fl_object
from flange.primitives.internal import Path, Solution
from flange.exceptions import ResolutionError

class _resolvable(fl_object):
    def print_tree(self):
        if isinstance(self._op, (list, tuple)):
            return (type(self), hex(id(self)), tuple([v.print_tree() if hasattr(v, 'print_tree') else v for v in self._op]))
        return type(self), hex(id(self))
    def __init__(self, op, raw): self._op, self._raw = op, raw
    def __union__(a, b):
        return Or([a, b], ['or', a._raw, b._raw])
    def __intersection__(a, b):
        return And([a, b], ['and', a._raw, b._raw])
    def __complement__(self): raise NotImplementedError()
    def resolve(self): raise NotImplementedError()
    def gather(self):
        msg = "Cannot 'gather' the result of '{}'".format(self._op.__fl_type__)
        raise ResolutionError(msg)

class Exists(_resolvable):
    def resolve(self):
        for x in self._op.resolve():
            yield x
    def __complement__(self):
        return Forall(Not(self._op))

class Forall(_resolvable):
    def resolve(self):
        yield Solution(sum([x.paths for x in self._op.resolve()], []), {})
    def __complement__(self):
        return Exists(Not(self._op))

class Gather(Exists):
    def resolve(self):
        return (x for x in self._op.gather())

class And(_resolvable):
    def resolve(self):
        for r1 in self._op[0].resolve():
            for r2 in self._op[1].resolve():
                yield r1 & r2
    def gather(self):
        return (r1 & r2 for r1 in self._op[0].gather() for r2 in self._op[1].gather())
    def __complement__(self):
        return Or([Not(self._op[0]), Not(self._op[1])])
    def __repr__(self):
        return repr(('And', self._op[0], self._op[1]))

class Or(_resolvable):
    def resolve(self):
        for result in self._op[0].resolve():
            yield result
        for result in self._op[1].resolve():
            yield result
    def gather(self):
        for result in self._op[0].gather(): yield result
        for result in self._op[1].gather(): yield result
    def __complement__(self):
        return And([Not(self._op[0]), Not(self._op[1])])
    def __repr__(self):
        return repr(('Or', self._op[0], self._op[1]))

class Not(_resolvable):
    def resolve(self):
        for result in self._op.resolve():
            result.negate()
            yield result
    def __complement__(self):
        return self._op
    def __repr__(self):
        return repr(('Not', self._op))
