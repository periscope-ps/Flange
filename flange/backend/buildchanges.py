from flange.primitives.resolvable import _resolvable
from flange.exceptions import CompilerError,ResolutionError

def run(program, env):
    results, interest = [], []
    for op in program:
        result = None
        if not isinstance(op, _resolvable):
            raise SyntaxError("Operation cannot be resolved into graph")
        for solution in op.resolve():
            tmpinterest = []
            try:
                for mod in env.get('mods', []):
                    solution, i = mod(solution, env)
                    tmpinterest.extend(i)
                result = solution
                interest += tmpinterest
                break
            except ResolutionError as e:
                if env.get('logging', 0) >= 1:
                    print("  [ResolutionError]", e)
                continue

        if not result:
            raise CompilerError("No solution found!")
        results.append(result)
        
    return results, interest
