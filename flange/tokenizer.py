import re

from lace.logging import trace

"""
tokenizer takes a list of expressions and for 
each one converts the expression string into 
a list of tokens.
"""

@trace.debug("tokenizer")
def _tokenize(line, sep, keep=False):
    return list(filter(None, re.split(sep, line)))
    
@trace.debug("tokenizer")
def _merge(line, lineno):
    result = []
    for token in line:
        if token == "=":
            if not result:
                raise SyntaxError("Line may not start with '=' [line {}]".format(lineno))
            if result[-1] in ["=", "<", ">", "!"]:
                result[-1] += "="
            else:
                result.append(token)
        else:
            result.append(token)
    return result

@trace.debug("tokenizer")
def _merge_num(line, lineno):
    result = []
    gen = iter(line)
    while True:
        try:
            token = next(gen)
            if token == ".":
                try: nxt = next(gen)
                except StopIteration: raise SyntaxError("Invalid syntax [line {}]".format(lineno))
                try: prv = result.pop()
                except IndexError: prv = 0

                try:
                    nxt, prv = int(nxt), int(prv)
                    result.append("{}.{}".format(prv, nxt))
                except ValueError:
                    result.extend([prv, ".", nxt])
            else:
                result.append(token)
        except StopIteration: break
    return result

@trace.debug("tokenizer")
def _merge_str(line, lineno):
    result = []
    sofar = ""
    for token in line:
        if sofar:
            if token[-1] in ["'", '"'] and token[-1] == sofar[0]:
                result.append(sofar + token)
                sofar = ""
            else:
                sofar += token
        else:
            if token[0] in ["'", '"'] and token[0] != token[-1]:
                sofar = token
            else:
                result.append(token)
    if sofar:
        raise SyntaxError("Unmatched quote [line {}]".format(lineno))
    return result

@trace.debug("tokenizer")
def _remove_ws(line):
    return list(filter(lambda x: not re.match("\s+", x), line))

# in: list of program lines
@trace.info("tokenizer")
def run(program, env):
    result = []
    for lnum, token in enumerate(program):
        _nospace = _tokenize(token, "(\s+)")
        result.append([])
        for itok in _nospace:
            result[-1].extend(_tokenize(itok, "(\||&|=|!=|<|>|{|}|\[|\]|\+|-|/|\*|~|\(|\)|\.|,|:)"))
        result[-1] = _merge(result[-1], lnum)
        result[-1] = _merge_str(result[-1], lnum)
        result[-1] = _merge_num(result[-1], lnum)
        result[-1] = _remove_ws(result[-1])
    return result


if __name__ == "__main__":
    test = [
        "let x = { name == 'v' }",
        "let y = { name==test('g')} ~> x",
        "x >= y",
        "exists x and y or y ~> x"
    ]
    
    print(run(test))
