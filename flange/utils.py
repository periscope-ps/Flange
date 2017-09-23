import re

def grammar(re_str, line, lines, handlers):
    groups = re.match(re_str, line[1])
    if not groups:
        raise SyntaxError("Bad Syntax [line {}] - {}".format(*line))
        
    if groups.group("op") in handlers:
        return handlers[groups.group("op")](line, lines)
    else:
        return handlers["default"](line, lines)
        
