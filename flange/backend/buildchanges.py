from functools import reduce

from flange.primitives.ops import _operation
from flange.exceptions import CompilerError,ResolutionError

def run(program, env):
    paths, rejected = [], []
    for op in program:
        path = None
        if not isinstance(op, _operation):
            raise SyntaxError("Operation cannot be resolved into graph")
        for delta in op.__fl_next__():
            #rejected.extend(delta.rejected)
            try:
                path = reduce(lambda x,mod: mod(x, env), env.get('mods', []), delta)
                break
            except ResolutionError as e:
                if env.get('logging', 0) >= 1:
                    print("  [ResolutionError]", e)
                #rejected.append(delta)
                continue

        if not path:
            raise CompilerError("No solution found!")
        paths.append(path)
        
    return paths, rejected
