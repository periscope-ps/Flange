from flange.tools.token import Token
from flange.exceptions import FlangeSyntaxError

from collections import defaultdict

"""
Pass 1: Tokenize

Takes a single string program and returns the list of tokens.
Token is implemented as a state machine and generates token based 
on a ``stack`` storing the current working token.  Each transition
contains a next state and stack actions, which may be any combination
of ``PUSH`` and ``YIELD``.

+-------+-----------------------------------------------------+
| PUSH  | Add the read character to the working stack         |
+-------+-----------------------------------------------------+
| YIELD | Add the current working stack to the list of tokens |
+-------+-----------------------------------------------------+

:class:`Tokens <flange.tools.token.Token>` are generated on each 
``YIELD`` instruction and store line and character information
for debugging.

This pass raises an error if the EOF is reached while still in 
a string state.


**Rules**

 - Whitespace is removed
 - Strings generate a single token
   - Both single and double quoted strings are allowed and uniquely close ('"' and "'" are valid)
   - ``\`` escapes a string ("\"" is valid)
 - [.0-9] yield single tokens containing any valid real number ( .5 notation allowed)
 - [:)([\]+-/*%] all act as token delimiters.
 - [<>!~] have the special property of optionally combining with an ``=`` to form a single token

**Returns**

``exists flow x, node a, node b: x(a, b)``

yields

[Token('exists', 0, 0), Token('flow', 7, 0), Token('x', 12, 0), Token(',', 8, 0),
 Token('node', 10, 0), Token('a', 15, 0), Token(',', 16, 0), Token('node', 18, 0),
 Token('b', 23, 0), Token(':', 24, 0), Token('x', 26, 0), Token('(', 27, 0),
 Token('a', 28, 0), Token(',', 29, 0), Token('b', 31, 0), Token(')', 32, 0)]

"""

PUSH,YIELD = 0,1
def_trans = {"base": ["base", [PUSH]],
             "combine": ["base", [YIELD, PUSH]],
             "num": ["base", [YIELD, PUSH]],
             "single_string": ["single_string", [PUSH]],
             "double_string": ["double_string", [PUSH]],
             "single_escape": ["single_string", [PUSH]],
             "double_escape": ["double_string", [PUSH]]}
trans = {"base": ["base", [YIELD, PUSH, YIELD]],
         "combine": ["base", [YIELD, PUSH, YIELD]],
         "num": ["base", [YIELD, PUSH, YIELD]],
         "single_string": ["single_string", [PUSH]],
         "double_string": ["double_string", [PUSH]],
         "single_escape": ["single_string", [PUSH]],
         "double_escape": ["double_string", [PUSH]]}
c_trans = {"base": ["combine", [YIELD, PUSH]],
           "combine": ["combine", [PUSH]],
           "num": ["combine", [YIELD, PUSH]],
           "single_string": ["single_string", [PUSH]],
           "double_string": ["double_string", [PUSH]],
           "single_escape": ["single_string", [PUSH]],
           "double_escape": ["double_string", [PUSH]]}
n_trans = {"base": ["num", [YIELD, PUSH]],
           "combine": ["num", [YIELD, PUSH]],
           "num": ["num", [PUSH]],
           "single_string": ["single_string", [PUSH]],
           "double_string": ["double_string", [PUSH]],
           "single_escape": ["single_string", [PUSH]],
           "double_escape": ["double_string", [PUSH]]}
ss_trans = {"base": ["single_string", [YIELD, PUSH, YIELD]],
            "combine": ["single_string", [YIELD, PUSH, YIELD]],
            "num": ["single_string", [YIELD, PUSH, YIELD]],
            "single_string": ["base", [YIELD, PUSH, YIELD]],
            "double_string": ["double_string", [PUSH]],
            "single_escape": ["single_string", [PUSH]],
            "double_escape": ["double_string", [PUSH]]}
ds_trans = {"base": ["double_string", [YIELD, PUSH, YIELD]],
            "combine": ["double_string", [YIELD, PUSH, YIELD]],
            "num": ["double_string", [YIELD, PUSH, YIELD]],
            "single_string": ["single_string", [PUSH]],
            "double_string": ["base", [YIELD, PUSH, YIELD]],
            "single_escape": ["single_string", [PUSH]],
            "double_escape": ["double_string", [PUSH]]}
e_trans = {"base": ["base", [YIELD, PUSH, YIELD]],
           "combine": ["base", [YIELD, PUSH, YIELD]],
           "num": ["base", [YIELD, PUSH, YIELD]],
           "single_string": ["single_escape", [PUSH]],
           "double_string": ["double_escape", [PUSH]],
           "single_escape": ["single_string", [PUSH]],
           "double_escape": ["double_string", [PUSH]]}
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
                if a == YIELD and stack:
                    yield Token(stack, ln, i)
                    i, stack = None, ""
                elif a == PUSH:
                    if isinstance(i, type(None)):
                        i = j
                    stack += c
        if state in ["single_string", "double_string"]:
            raise FlangeSyntaxError("reached EOL while scanning string literal", Token(line[i:], ln, i))
        if stack:
            yield Token(stack, ln, i)

def run(program, env):
    return list(filter(lambda x: x.val and x.val not in ws, _build_tokens(program)))
