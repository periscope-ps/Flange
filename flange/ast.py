from lace.logging import trace

"""
ast takes each list of tokens and converts the expression 
into an abstract syntax tree (tok, block, ...)

toks:

extern
type
flow
query
exists
forall
gather
app
index
not
and
or
var
bool
string
number
*
+
-
/
==
!=
<
<=
>
>=
"""

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
def _match_all(ops, inst, lno):
    for head,op in ops.items():
        resolver = _match(op, inst, lno)
        if resolver:
            return resolver(head)

@trace.debug("ast")
def _match_until(start, inst, name, lno):
    parens = _pcount()
    valid = True
    for i in range(start, len(inst)):
        if inst[i] == name and valid:
            return (start, i)
        try:
            valid = not parens.isNested(inst[i], lno)
        except SyntaxError:
            break
    return False

@trace.debug("ast")
def _match(op, inst, lno):
    tups = []
    start = 0
    for i, v in enumerate(op):
        if isinstance(v, str):
            if inst[start] != v:
                return False
            start += 1
        else:
            if len(op) != i + 1:
                match = _match_until(start, inst, op[i+1], lno)
                if match:
                    tups.append((inst[match[0]:match[1]], v))
                    start = match[1]
                else:
                    return False
            else:
                tups.append((inst[start:], v))
    
    def _resolve(head):
        result = [head]
        for inst, op in tups:
            result.append(op(inst, lno))
        return tuple(result)
        
    return _resolve

@trace.debug("ast")
def _csl(inst, lno):
    parens = _pcount()
    current = 0
    results = []
    for i, v in enumerate(inst):
        if not parens.isNested(v, lno) and v == ',':
            results.append(logic_or(inst[current:i], lno))
            current = i+1
    if inst:
        results.append(logic_or(inst[current:], lno))
    return results
    
def unnest(f):
    def _f(inst, lno):
        if not inst: raise SyntaxError("Invalid syntax [line {}]".format(lno))
        if inst[0] == "(" and inst[-1] == ")":
            parens = _pcount()
            for v in inst[:-1]:
                if not parens.isNested(v, lno):
                    return f(inst, lno)
            return f(inst[1:-1], lno)
        return f(inst, lno)
    return _f

@unnest
@trace.info("ast")
def logic_not(inst, lno):
    return _match_all({"not": ("not", logic_or)}, inst, lno) or expr(inst, lno)
@unnest
@trace.info("ast")
def logic_or(inst, lno):
    return _match_all({"or": (logic_or, "or", logic_or)}, inst, lno) or logic_and(inst, lno)
@unnest
@trace.info("ast")
def logic_and(inst, lno):
    return _match_all({"and": (logic_or, "and", logic_or)}, inst, lno) or logic_not(inst, lno)

@unnest
@trace.info("ast")
def expr(inst, lno):
    patterns = {
        "exists": ("exists", logic_or),
        "forall": ("forall", logic_or),
        "gather": ("gather", logic_or)
    }
    result = _match_all(patterns, inst, lno)
    if not result:
        return logic_flow(inst, lno)
    return result

@trace.info("ast")
def logic_flow(inst, lno):
    resolver = _match((query, "~", ">", logic_flow), inst, lno)
    if resolver:
        flow = resolver("flow")
        return ("flow", (), flow[1], flow[2])
    resolver = _match((query, "~", query, ">", logic_flow), inst, lno)
    if resolver:
        flow = resolver("flow")
        return ("flow", flow[2], flow[1], flow[3])
    return logic_comp(inst, lno)
@trace.info("ast")
def logic_comp(inst, lno):
    patterns = {
        "==": (logic_or, "==", logic_or),
        "!=": (logic_or, "!=", logic_or),
        "<":  (logic_or, "<" , logic_or),
        "<=": (logic_or, "<=", logic_or),
        ">":  (logic_or, ">", logic_or),
        ">=": (logic_or, ">=", logic_or)
    }
    return _match_all(patterns, inst, lno) or math_add(inst, lno)
@unnest
@trace.info("ast")
def math_add(inst, lno):
    return _match_all({ "+": (math_add, "+", math_add), "-": (math_add, "-", math_add) }, inst, lno) or math_mult(inst, lno)
@trace.info("ast")
def math_mult(inst, lno):
    return _match_all({ "*": (math_add, "*", math_add), "/": (math_add, "/", math_add), "%": (math_add, "%", math_add) }, inst, lno) or app(inst, lno)
@trace.info("ast")
def app(inst, lno):
    return _match_all({"app": (app, "(", _csl, ")")}, inst, lno) or index(inst, lno)
@trace.info("ast")
def index(inst, lno):
    return _match_all({"index": (app, "[", logic_or, "]")}, inst, lno) or attr(inst, lno)
@trace.info("ast")
def attr(inst, lno):
    parens = _pcount(reverse=True)
    for start in reversed(range(len(inst))):
        if not parens.isNested(inst[start], lno):
            if inst[start] == ".":
                return ("attr", logic_or(inst[start+1:], lno), logic_or(inst[:start], lno))
    return query(inst, lno)

@trace.info("ast")
def query(inst, lno):
    resolver = _match(("{", var, "in", query, "|", logic_or, "}"), inst, lno)
    if resolver:
        flow = resolver("query")
        return ("query", flow[1][1], flow[2], flow[3])
    resolver = _match(("{", var, "|", logic_or, "}"), inst, lno)
    if resolver:
        flow = resolver("query")
        return ("query", flow[1][1], (), flow[2])
    return ls(inst, lno)

@trace.info("ast")
def ls(inst, lno):
    parens = _pcount()
    if inst[0] == '[' and inst[-1] == ']':
        for v in inst[:-1]:
            if not parens.isNested(v, lno):
                return terms(inst, lno)
        result = ["list"]
        result.extend(_csl(inst[1:-1], lno))
        return result
    return terms(inst, lno)

@trace.info("ast")
def terms(inst, lno):
    if len(inst) == 1:
        if inst[0] in ["True", "False"]:
            return ("bool", inst[0] == "True")
        if inst[0] == "None":
            return ("empty", None)
        try: return ("number", float(inst[0]))
        except ValueError: pass
        if inst[0][0] in ['"', "'"]:
            if inst[0][-1] == inst[0][0]:
                return ("string", inst[0][1:-1])
            else:
                raise SyntaxError("Unmatched quotes [line {}]".format(lno))
        else:
            return var(inst, lno)
    raise SyntaxError("Invalid syntax [line {}] - {}".format(lno, inst))

@trace.info("ast")
def var(inst, lno):
    if len(inst) != 1 and not inst[0][0].isdigit():
        raise SyntaxError("Invalid variable name [line {}] - {}".format(lno, inst))
    return ("var", inst[0])

@trace.info("ast")
def program(inst, lno):
    patterns = {
        "extern": ("extern", lambda x,y: ("type", x[0], x[1])),
        "let": ("let", lambda x,y: x[0], "=", logic_or),
    }
    result = _match_all(patterns, inst, lno)
    if not result:
        return logic_or(inst, lno)
    return result

# in: a list of lines, each line a list of tokens
# out: a f-ast
@trace.info("ast")
def run(insts, env):
    ast = []
    for lnum, inst in enumerate(insts):
        ast.append(program(inst, lnum+1))
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
