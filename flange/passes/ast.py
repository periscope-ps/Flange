from flange.exceptions import FlangeSyntaxError
from flange.passes.ast_utils import match, exact, SkipInstance
from flange.tools.block import Block
from flange.types import fl_lift

from collections import namedtuple

_rule  = namedtuple("_rule", ['tag', 'v'])
_state = namedtuple("_state", ['rules', 'options', 'exception'])
_state.__new__.__defaults__ = (None,"")
states = {
    "expr":    _state([]),
    "exists":  _state([_rule("exists", ('exists', match('varlist'), ':', match('expr')))]),
    "forall":  _state([_rule("forall", ('forall', match('varlist'), ':', match('expr')))]),
    "varlist": _state([_rule("varlist", (match('varpair'), ',', match('varlist')))]),
    "varpair": _state([_rule("varpair", (exact('type'), exact('sym')))], [],
                      " - Parameter list must be in the form of <type> <name>"),
    "vallist": _state([_rule("vallist", (match('expr'), ',', match('vallist')))]),
    "empty":   _state([_rule("", ('',))], ["empty"]),
    "or":      _state([_rule("or", (match('expr'), 'or', match('expr')))]),
    "and":     _state([_rule("and", (match('expr'), 'and', match('expr')))]),
    "not":     _state([_rule("not", ('not', match('expr')))]),
    "implies": _state([_rule("implies", (match('expr'), 'if', match('expr'), 'else', match('expr'))),
                       _rule("implies", (match('expr'), 'if', match('expr')))]),
    "cmp":     _state([_rule("=", (match('expr'), '=', match('expr'))),
                      _rule("!=", (match('expr'), '!=', match('expr'))),
                      _rule(">", (match('expr'), '>', match('expr'))),
                      _rule(">=", (match('expr'), '>=', match('expr'))),
                      _rule("<", (match('expr'), '<', match('expr'))),
                      _rule("<=", (match('expr'), '<=', match('expr')))]),
    "flowcat": _state([_rule("flow", (exact('sym'), '~>', match('flowcat')))]),
    "math_t1": _state([_rule("+", (match('math_t1'), '+', match('math_t1'))),
                       _rule("-", (match('math_t1'), '-', match('math_t1')))]),
    "math_t2": _state([_rule("*", (match('math_t1'), '*', match('math_t1'))),
                       _rule("/", (match('math_t1'), '/', match('math_t1'))),
                       _rule('%', (match('math_t1'), '%', match('math_t1')))]),
    "math_b":  _state([_rule("", (exact("tok"),))], ["replace"]),
    "index":   _state([_rule("index", (match('expr'), '[', match('expr'), ']'))], ["reverse"]),
    "attr":    _state([_rule("attr", (match('expr'), '.', match('expr'))),
                       _rule("app", (match('expr'), exact(match('vallist'))))], ["reverse"]),
}

failure_transitions = {
    "expr": ["exists", "forall", "or", "flowcat", "math_t1", "index"],
    "exists": [],
    "forall": [],
    "varlist": ["varpair"],
    "varpair": [],
    "vallist": ["expr", "empty"],
    "or": ["and"],
    "and": ["not"],
    "not": ["implies"],
    "implies": ["cmp"],
    "cmp": [],
    "flowcat": ["math_b"],
    "math_t1": ["math_t2"],
    "math_t2": ["math_b"],
    "math_b": [],
    "index": ["attr"],
    "attr": []
}

def _do_block(n, state_name):
    state = states[state_name]
    options = state.options or []
    def _rev(ls):
        return list(reversed(ls)) if 'reverse' in options else list(ls)
    ls, rules = _rev(n.tokens), [_rev(r.v) for r in state.rules]
    matches, fns = [[] for _ in range(len(rules))], [[] for _ in range(len(rules))]
    first = [(i, len(ls)) for i in range(len(rules))]

    if "empty" in options and len(ls) == 0:
        return n
    
    # Group tokens by delimiter
    for j, r in enumerate(rules):
        for i, t in enumerate(ls):
            if r and r[0] == t.val:
                first[j], _ = (j, min(first[j][1], i)), r.pop(0)
            else:
                fn = None
                if r and isinstance(r[0], match):
                    fn, _ = r.pop(0), matches[j].append([])
                if not matches[j]: break
                matches[j][-1].append(t)
                if fn:
                    fns[j].append(fn)
                    if isinstance(fn, exact):
                        matches[j].append([])

    # Search for first full match
    for i, _ in sorted(first, key=lambda x: x[1]):
        m = list(filter(bool, matches[i]))
        if len(m) != len(fns[i]) or rules[i]: continue
        try:
            groups = _rev([fn(_rev(m[j])) for j, fn in enumerate(fns[i])])
        except SkipInstance:
            continue
        if "replace" in options:
            return groups[0]
        n.tag, n.tokens = state.rules[i].tag, groups
        return n

    # Search next states in chain for match
    msg = "Invalid Syntax" + str(state.exception)
    for n_state in failure_transitions[state_name]:
        try:
            return _do_block(n, n_state)
        except FlangeSyntaxError as exp:
            msg = msg if msg[17:] else exp.msg
            continue
    raise FlangeSyntaxError(msg, n)

def _visit(n):
    if isinstance(n, Block):
        return _do_block(n, getattr(n, 'state', 'expr'))
    else:
        return fl_lift(n)

def run(program, env):
    return program.apply(_visit)
