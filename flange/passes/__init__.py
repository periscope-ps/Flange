from flange.passes import token, group, ast

_passes = [token.run, group.run, ast.run]
def run(program, env, debug=False):
    if debug:
        print(program)
    for p in _passes:
        program = p(program, env)
        if debug:
            print(program)
    return program

