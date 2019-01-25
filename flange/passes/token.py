from flange.tools.token import Token
from flange.exceptions import FlangeSyntaxError

from collections import defaultdict

def_trans = {"base": ["base", ["push"]],
             "combine": ["base", ["yield", "push"]],
             "num": ["base", ["yield", "push"]],
             "single_string": ["single_string", ["push"]],
             "double_string": ["double_string", ["push"]],
             "single_escape": ["single_string", ["push"]],
             "double_escape": ["double_string", ["push"]]}
trans = {"base": ["base", ["yield", "push", "yield"]],
         "combine": ["base", ["yield", "push", "yield"]],
         "num": ["base", ["yield", "push", "yield"]],
         "single_string": ["single_string", ["push"]],
         "double_string": ["double_string", ["push"]],
         "single_escape": ["single_string", ["push"]],
         "double_escape": ["double_string", ["push"]]}
c_trans = {"base": ["combine", ["yield", "push"]],
           "combine": ["combine", ["push"]],
           "num": ["combine", ["yield", "push"]],
           "single_string": ["single_string", ["push"]],
           "double_string": ["double_string", ["push"]],
           "single_escape": ["single_string", ["push"]],
           "double_escape": ["double_string", ["push"]]}
n_trans = {"base": ["num", ["yield", "push"]],
           "combine": ["num", ["yield", "push"]],
           "num": ["num", ["push"]],
           "single_string": ["single_string", ["push"]],
           "double_string": ["double_string", ["push"]],
           "single_escape": ["single_string", ["push"]],
           "double_escape": ["double_string", ["push"]]}
ss_trans = {"base": ["single_string", ["yield", "push", "yield"]],
            "combine": ["single_string", ["yield", "push", "yield"]],
            "num": ["single_string", ["yield", "push", "yield"]],
            "single_string": ["base", ["yield", "push", "yield"]],
            "double_string": ["double_string", ["push"]],
            "single_escape": ["single_string", ["push"]],
            "double_escape": ["double_string", ["push"]]}
ds_trans = {"base": ["double_string", ["yield", "push", "yield"]],
            "combine": ["double_string", ["push", "yield"]],
            "num": ["double_string", ["yield", "push", "yield"]],
            "single_string": ["single_string", ["push"]],
            "double_string": ["base", ["yield", "push", "yield"]],
            "single_escape": ["single_string", ["push"]],
            "double_escape": ["double_string", ["push"]]}
e_trans = {"base": ["base", ["yield", "push", "yield"]],
           "combine": ["base", ["yield", "push", "yield"]],
           "num": ["base", ["yield", "push", "yield"]],
           "single_string": ["single_escape", ["push"]],
           "double_string": ["double_escape", ["push"]],
           "single_escape": ["single_string", ["push"]],
           "double_escape": ["double_string", ["push"]]}
states = {
    " ": trans, "\n": trans, "\t": trans,
    "(": trans, ")": trans,
    ":": trans, "+": trans, "-": trans, "/": trans, "*": trans, "%": trans,
    "=": c_trans, "!": c_trans, ">": c_trans, "<": c_trans, "~": c_trans,
    ".": n_trans, "[": trans, "]": trans, ",": trans,
    "'": ss_trans, '"': ds_trans, "\\": e_trans,
    "0": n_trans, "1": n_trans, "2": n_trans, "3": n_trans, "4": n_trans,
    "5": n_trans, "6": n_trans, "7": n_trans, "8": n_trans, "9": n_trans,
}

ws = [" ", "\n", "\t"]
def _build_tokens(program):
    for ln, line in enumerate(program.split("\n")):
        stack, state, i = "", "base", 0
        for j, c in enumerate(line):
            state, actions = states.get(c, def_trans)[state]
            for a in actions:
                if a == "yield" and stack:
                    yield Token(stack, ln, i)
                    i, stack = None, ""
                elif a == "push":
                    if isinstance(i, type(None)):
                        i = j
                    stack += c
        if state in ["single_string", "double_string"]:
            raise FlangeSyntaxError("reached EOL while scanning string literal", Token(line[i:], ln, i))
        if stack:
            yield Token(stack, ln, i)

def run(program, env):
    return list(filter(lambda x: x.val and x.val not in ws, _build_tokens(program)))
