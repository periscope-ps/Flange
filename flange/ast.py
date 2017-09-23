from lace.logging import trace

# Logic
@trace.debug("ast")
class _pcount(object):
    def __init__(self, reverse=False):
        self.counts = [0, 0, 0]
        self.open = ["]", ")", "}"] if reverse else ["[", "(", "{"]
        self.close = ["[", "(", "{"] if reverse else ["]", ")", "}"]
    def isNested(self, token, lineno):
        if token in self.open:
            self.counts[self.open.index(token)] += 1
        elif token in self.close:
            self.counts[self.close.index(token)] -= 1
            if any(map(lambda x: x < 0, self.counts)):
                raise SyntaxError("Unmatched brackets [line {}]".format(lineno))
        return any(map(lambda x: x != 0, self.counts))
        
@trace.debug("ast")
def _split_on(inst, sep, cb1, cb2, lineno, tag=None):
    _parens = _pcount()
    if not inst:
        raise SyntaxError("too few arguments [line {}]".format(lineno))
    for i in range(len(inst)):
        if not _parens.isNested(inst[i], lineno) and inst[i] in sep:
            return (tag or inst[i], cb1(inst[:i], lineno), cb1(inst[i+1:], lineno))
    return cb2(inst, lineno)

@trace.debug("ast")
def _logic(inst, lineno):
    return _split_on(inst, ["or"], _logic, _logic_and, lineno)
@trace.debug("ast")
def _logic_and(inst, lineno):
    return _split_on(inst, ["and"], _logic_and, _logic_flow, lineno)
@trace.debug("ast")
def _logic_flow(inst, lineno):
    _outer_parens = _pcount()
    for start in range(len(inst)):
        if not _outer_parens.isNested(inst[start], lineno) and inst[start] == "~":
            _inner_parens = _pcount()
            for end in range(start, len(inst)):
                if not _inner_parens.isNested(inst[end], lineno) and inst[end] == ">":
                    conds = _expr(inst[start+1:end], lineno) if start+1 != end else []
                    return ("flow", conds, _logic(inst[:start], lineno), _logic(inst[end+1:], lineno))
            raise SyntaxError("Unmatched flow arrow (missing >) [line {}]".format(lineno))
    return _logic_comp(inst, lineno)
@trace.debug("ast")
def _logic_comp(inst, lineno):
    return _split_on(inst, ["==", "!=", "<", "<=", ">", ">="], _logic_comp, _math_add, lineno)
@trace.debug("ast")
def _math_add(inst, lineno):
    return _split_on(inst, ["+", "-"], _math_add, _math_mult, lineno)
@trace.debug("ast")
def _math_mult(inst, lineno):
    return _split_on(inst, ["*", "/", "%"], _math_mult, _unary, lineno)
@trace.debug("ast")
def _unary(inst, lineno):
    if inst[0] in ["not"]:
        return ("not", _unary(inst[1:], lineno))
    return _app(inst, lineno)
@trace.debug("ast")
def _app(inst, lineno):
    _parens = _pcount(reverse=True)
    if inst[-1] == ")":
        for start in reversed(range(len(inst))):
            if not _parens.isNested(inst[start], lineno):
                if start != 0:
                    return ("app", _logic(inst[:start], lineno), tuple(_list(inst[start+1:-1], lineno)))
                else:
                    return _attr(inst, lineno)
        raise SyntaxError("Unmatched parens in function [line {}]".format(lineno))

    return _attr(inst, lineno)
@trace.debug("ast")
def _attr(inst, lineno):
    _parens = _pcount(reverse=True)
    if inst[-1] == "]":
        for start in reversed(range(len(inst))):
            if not _parens.isNested(inst[start], lineno):
                if start != 0:
                    return ("index", _logic(inst[:start], lineno), _logic(inst[start+1:-1], lineno))
    _parens = _pcount(reverse=True)
    for start in reversed(range(len(inst))):
        if not _parens.isNested(inst[start], lineno):
            if inst[start] == ".":
                return ("attr", _logic(inst[:start], lineno), _logic(inst[start+1:], lineno))
    return _expr(inst, lineno)

# Expr
@trace.debug("ast")
def _expr(inst, lineno):
    if not inst:
        raise SyntaxError("Expected expression [line {}]".format(lineno))
    elif len(inst) == 1:
        if inst[0] in ["True", "False"]:
            return ("bool", inst[0])
        if inst[0] == "None":
            return ("empty", None)
        if inst[0].isdigit():
            return ("number", int(inst[0]))
        if inst[0][0] in ['"', "'"]:
            if inst[0][-1] == inst[0][0]:
                return ("string", inst[0][1:-1])
            else:
                raise SyntaxError("Unmatched quotes [line {}]".format(lineno))
        else:
            return ("var", inst[0])
    else:
        if inst[0] == "{":
            if inst[-1] == "}":
                return ("query", _logic(inst[1:-1], lineno))
            else:
                raise SyntaxError("Unmatched braces in query [line {}]".format(lineno))
        if inst[0] == "(":
            for i in range(len(inst)):
                if inst[i] == ")":
                    break
            if inst[-1] == ")" and i == len(inst) - 1:
                return _logic(inst[1:-1], lineno)
        elif inst[0] == "[":
            for i in range(len(inst)):
                if inst[i] == "]":
                    break
            if inst[-1] == "]":
                if i == len(inst) - 1:
                    result = ["list"]
                    result.extend(_list(inst[1:-1], lineno))
                    return tuple(result)
            else:
                raise SyntaxError("Unmatched bracket in list [line {}]".format(lineno))
        else:
            for token in inst:
                if token == ":":
                    return _path(inst, lineno)
                elif token in ["and", "or", "not", "+", "-", "*", "/", "%", "==", "!=", "<=", "<", ">", ">="]:
                    return _logic(inst, lineno)
        raise SyntaxError("Unknown Syntax [line {}] - {}".format(lineno, inst))

@trace.debug("ast")
def _path(inst, lineno):
    for i in range(len(inst)):
        if inst[i] == ":":
            return ("path", _expr(inst[:i], lineno), _expr(inst[i+1:], lineno))
@trace.debug("ast")
def _list(inst, lineno):
    start = 0
    results = []
    for i in range(len(inst)):
        if inst[i] == ",":
            results.append(_expr(inst[start:i], lineno))
            start = i + 1
    if start != len(inst):
        results.append(_expr(inst[start:], lineno))
    return results

@trace.debug("ast")
def _let(inst, lineno):
    try:
        return ("let", inst[1], _logic(inst[3:], lineno))
    except IndexError:
        raise SyntaxError("let contains too few arguments [line {}]".format(lineno))


# Decl
@trace.debug("ast")
def _decl(inst, lineno):
    return ("exists", _logic(inst[1:], lineno))

@trace.debug("ast")
def _program(inst, lineno):
    if inst[0] == "let":
        return _let(inst, lineno)
    if inst[0] in ["exists"]:
        return _decl(inst, lineno)
    else:
        return _logic(inst, lineno)

# in: a list of lines, each line a list of tokens
# out: a f-ast
@trace.info("ast")
def run(program):
    ast = []
    for lnum, inst in enumerate(program):
        ast.append(_program(inst, lnum+1))
    return ast

if __name__ == "__main__":
    from pprint import pprint
    test = [['let', 'x', '=', '{', 'name', '==', '"b"', '}'],
            ['let', 'y', '=', '{', 'name', '>', '400', '}'],
            ['let', 'f', '=', 'x', '~', '>', 'y'],
            ['exists', 'x', '~', '{', 'test', '==', 'True', '}', '>', 'y'],
            ['exists', 'f']]
    pprint(test)
    pprint(run(test))
