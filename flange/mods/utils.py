from flange.primitives.internal import Solution

from functools import wraps

def only(n):
    def wrapper(f):
        @wraps(f)
        def _f(solution, env):
            result, interest = f(Solution([p for p in solution.paths if p[0] == n], solution.env), env)
            result.paths.extend([p for p in solution.paths if p[0] != n])
            return result, interest
        return _f
    return wrapper
