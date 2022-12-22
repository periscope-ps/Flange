from flange.passes import token, group, ast, uniquify, facttree, types
import sys, logging

_passes = [token.run, group.run, ast.run, uniquify.run, types.run, facttree.run]
log = logging.getLogger("flange.passes")
def run(program, env, debug=False):
    log.debug(program)
    for p in _passes:
        if debug: log.debug(f"\n{p.__module__.upper()}:")
        program = p(program, env)
        log.debug(program)
    return program

