from flange.tools import Block, Token, Symbol
from flange.exceptions import FlangeSyntaxError

n = 0
def _getvars(node):
    global n
    match node:
        case Block("varpair", toks):
            name = toks[1].val
            n, toks[1].val = n+1, f"{name}.{n}"
            return [Block("varpair", (toks[0], toks[1]))], {name: toks[1].val}
        case Block("varlist", toks):
            left, right = _getvars(toks[0]), _getvars(toks[1])
            return (left[0] + right[0]), {**left[1], **right[1]}

def _run(node, env):
    match node:
        case Block("exists", toks) | Block("forall", toks):
            binds, names = _getvars(toks[0])
            local = {**{k:v for k,v in env.items()}, **names}
            node.tokens = (Block(tag="varlist", tokens=tuple(binds)), _run(toks[1], local))
        case Symbol(val=val):
            if val not in env:
                raise FlangeSyntaxError(f"Unknown variable name '{val}'", node)
            node.val = env[val]
        case Block("attr", toks):
            node.tokens = (_run(toks[0], env), toks[1])
        case Block("app", toks):
            # TODO Function linking
            node.tokens = (toks[0], _run(toks[1], env))
        case Token():
            pass
        case _:
            node.tokens = [_run(t, env) for t in node.tokens]
    return node

def run(node, env):
    return _run(node, {})
