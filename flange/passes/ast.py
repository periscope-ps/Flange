from flange.exceptions import FlangeSyntaxError
from flange.tools.ast_utils import match, exact, SkipInstance
from flange.tools import fl_lift

from collections import namedtuple

_rule  = namedtuple("_rule", ['tag', 'v'])
_state = namedtuple("_state", ['rules', 'options', 'exception'])
_state.__new__.__defaults__ = (None,"")
states = {
    "expr":    _state([]),
    "exists":  _state([_rule("exists", ('exists', match('varlist'), ':', match('expr'))),
                       _rule("forall", ('forall', match('varlist'), ':', match('expr'))),
                       _rule("or", (match('expr'), 'or', match('expr'))),
                       _rule("and", (match('expr'), 'and', match('expr')))]),
    "varlist": _state([_rule("varlist", (match('varpair'), ',', match('varlist')))]),
    "varpair": _state([_rule("varpair", (exact('type'), exact('sym')))], [],
                      " - Parameter list must be in the form of <type> <name>"),
    "vallist": _state([_rule("vallist", (match('expr'), ',', match('vallist')))]),
    "empty":   _state([_rule("", ('',))], ["empty"]),
    "not":     _state([_rule("not", ('not', match('expr')))]),
    "implies": _state([_rule("implies", (match('expr'), 'if', match('expr'), 'else', match('expr'))),
                       _rule("implies", (match('expr'), 'if', match('expr')))]),
    "cmp":     _state([_rule("==", (match('expr'), '==', match('expr'))),
                      _rule("!=", (match('expr'), '!=', match('expr'))),
                      _rule(">", (match('expr'), '>', match('expr'))),
                      _rule(">=", (match('expr'), '>=', match('expr'))),
                      _rule("<", (match('expr'), '<', match('expr'))),
                       _rule("<=", (match('expr'), '<=', match('expr'))),
                       _rule("in", (match('expr'), "in", match('expr')))]),
    "flowcat": _state([_rule("flow", (exact('sym'), '~>', match('flowcat')))]),
    "bw_or":   _state([_rule("|", (match('bw_xor'), '|', match('bw_or')))]),
    "bw_xor":  _state([_rule("^", (match('bw_and'), '^', match('bw_or')))]),
    "bw_and":  _state([_rule("&", (match('math_t1'), '&', match('bw_or')))]),
    "math_t1": _state([_rule("+", (match('math_t2'), '+', match('math_t1'))),
                       _rule("-", (match('math_t2'), '-', match('math_t1')))]),
    "math_t2": _state([_rule("*", (match('index'), '*', match('math_t1'))),
                       _rule("/", (match('index'), '/', match('math_t1'))),
                       _rule('%', (match('index'), '%', match('math_t1')))]),
    "math_b":  _state([_rule("", (exact("tok"),))], ["replace"]),
    "index":   _state([_rule("index", (match('expr'), '[', match('expr'), ']'))], ["reverse"]),
    "attr":    _state([_rule("attr", (match('expr'), '.', match('expr'))),
                       _rule("app", (match('expr'), exact(match('vallist'))))], ["reverse"]),
    "block":   _state([_rule("", (exact(match('expr')),))], ["replace"]),
}

failure_transitions = {
    "expr": ["block", "exists", "flowcat", "bw_or"],
    "exists": ["not"],
    "varlist": ["varpair"],
    "varpair": [],
    "vallist": ["expr", "empty"],
    "not": ["implies"],
    "implies": ["cmp"],
    "cmp": [],
    "flowcat": ["math_b"],
    "bw_or": ["bw_xor"],
    "bw_xor": ["bw_and"],
    "bw_and": ["math_t1"],
    "math_t1": ["math_t2"],
    "math_t2": ["index"],
    "math_b": [],
    "index": ["attr"],
    "attr": ["math_b"],
    "block": []
}

def rule_match(rule, toks, order):
    if len(rule) == 0:
        raise SkipInstance()
    result, matches, rule = [], [], ([r for r in rule] + [None])
    first, goal = float('inf'), rule.pop(0)
    group = goal
    for i, token in enumerate(toks):
        if isinstance(goal, match):
            if matches:
                first, matches, _ = min(first, i), [], result.append(group(order(matches)))
            group = goal
            try: goal = rule.pop(0)
            except IndexError: goal = None

        if token.val != goal:
            matches.append(token)
        else:
            if isinstance(group, match):
                result.append(group(order(matches)))
            elif matches:
                raise SkipInstance()
            try:
                first, matches, goal, group = min(first, i), [], rule.pop(0), None
            except IndexError: break
    if rule and rule[0] is not None:
        raise SkipInstance()
    if matches and group:
        result.append(group(matches))
    return first, result

def _do_block(n, state_name=None):
    if not hasattr(n, "tokens"):
        return fl_lift(n)
    state_name = state_name or getattr(n, 'tag', 'expr')
    state, options = states[state_name], (states[state_name].options or [])
    def _rev(ls):
        return list(reversed(ls)) if 'reverse' in options else list(ls)
    toks = _rev(n.tokens)

    if "empty" in options and len(toks) == 0:
        return n

    # Group tokens by delimiter
    matches = []
    for j, r in enumerate([_rev(r.v) for r in state.rules]):
        try: matches.append((state.rules[j], rule_match(r, toks, _rev)))
        except SkipInstance: pass

    # Select first match
    for rule, (_, groups) in sorted(matches, key=lambda x: x[1][0]):
        if len(groups) != len([m for m in rule.v if isinstance(m, match)]):
            continue
        groups = _rev(groups)
        if "replace" in options:
            if hasattr(groups[0], "tag"):
                return _do_block(groups[0], groups[0].tag)
            return groups[0]
        n.tag, n.tokens = rule.tag, groups
        return n

    # Search next states in chain for match
    msg = "Invalid Syntax" + str(state.exception)
    for n_state in failure_transitions[state_name]:
        try:
            return _do_block(n, n_state)
        except FlangeSyntaxError as exp:
            msg = msg if state.exception else exp.msg
            continue
    raise FlangeSyntaxError(msg, n)

def _visit(n):
    result = _do_block(n)
    if hasattr(result, "tokens"):
        result.tokens = [_visit(t) for t in result.tokens]
    return result

def run(program, env):
    program.tag = "expr"
    return _visit(program)
