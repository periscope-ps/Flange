from flange.tools.fact import Entity, FTreeNode, Fact, Quantifier, EntityType
from flange.tools import Block, Symbol
from flange.exceptions import FlangeSyntaxError

"""
BLOCKS
exists forall or and
not implies
varlist varpair vallist
in == != > >= < <=
flow
| ^ & + - * / %
index attr app
Token Type Symbol
"""

def _getfact(node, env):
    def _do(n):
        match n:
            case Symbol(val=val):
                return (n, n) if val in env else (None, None)
            case Block("app", toks):
                return None, _do(toks[1])[0]
            case Block(tag, toks):
                left, right = _do(toks[0]), _do(toks[1])
                return ((left[0] if left[0] is not None else left[1]),
                        (right[0] if right[0] is not None else right[1]))
            case _:
                return None, None
    left, right = _do(node)
    if left is None:
        if right is None:
            raise FlangeSyntaxError("Invalid expression, rule must include a network entity", node)
        return Fact(node.tag, right, node.tokens[1], node.tokens[0])
    else:
        return Fact(node.tag, left, node.tokens[0], node.tokens[1])

def _getentities(q, args):
    for tok in args.tokens:
        if tok.tokens[0].val == "node": yield Entity(q, EntityType.NODE, tok.tokens[1])
        else: yield Entity(q, EntityType.FLOW, tok.tokens[1])

def _run(node, tree, env):
    match node:
        # TODO Negation
        # TODO Implication
        case Block("exists", toks) | Block("forall", toks):
            ty = Quantifier.EXISTS if node.tag == "exists" else Quantifier.FORALL
            entities = tuple(_getentities(ty, toks[0]))
            tree.entities.extend(entities)
            return _run(toks[1], tree, {**env, **{e.name.val: e for e in entities}})
        case Block("or", toks):
            tree.children.extend([_run(toks[0], FTreeNode(), env), _run(toks[1], FTreeNode(), env)])
            return tree
        case Block("and", toks):
            return _run(toks[0], _run(toks[1], tree, env), env)
        case Block("==", toks) | Block("<", toks) | Block("<=", toks) | Block(">", toks) | \
             Block(">=", toks) | Block("!=", toks) | Block("in", toks) | Block("app", toks):
            subject, fact = None, _getfact(node, env)
            for entity in tree.entities:
                if entity.name == fact.ref.val:
                    subject = entity
                    break
            if subject is None:
                e = env[fact.ref.val]
                subject = Entity(e.quant, e.ty, e.name)
                tree.entities.append(subject)
            subject.facts.append(fact)
            return tree
        case _:
            return tree
def _collapse(node):
    n_ents = {}
    for e in node.entities:
        if e.name.val not in n_ents:
            n_ents[e.name.val] = e
        else:
            n_ents[e.name.val].facts.extend(e.facts)
    node.entities = n_ents.values()
    node.children = [_collapse(n) for n in node.children]
    return node

def _flatten(node):
    n_child = []
    for c in node.children:
        if c.entities:
           n_child.append(_flatten(c))
        else:
            n_child.extend([_flatten(cc) for cc in c.children])
    node.children = n_child
    return node

def run(program, env):
    return _flatten(_collapse(_run(program, FTreeNode(), {})))
