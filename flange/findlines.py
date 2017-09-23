from flange.utils import grammar

from lace.logging import trace

_syntax = {
    "var": "[_A-Za-z][_A-Za-z0-9!@#$%^*-]*",
    "decl": "exists "
}

@trace.debug("findlines")
def _compress_lines(comps, line, lines):
    result = line[1]
    while any([line[1].endswith(x) for x in comps]):
        try:
            line = list(next(lines))
            line[1] = line[1].strip()
            if not line[1]:
                continue
            result += " {}".format(line[1])
        except StopIteration:
            raise SyntaxError("Unexpected end of file [line {}]".format(line[0]))
    return result
    
@trace.debug("findlines")
def _make_let(line, lines):
    return _compress_lines([",", " and", " or"], line, lines)
@trace.debug("findlines")
def _make_exists(line, lines):
    return _compress_lines([",", " and", " or"], line, lines)
@trace.debug("findlines")
def _make_comp(line, lines):
    return _compress_lines([",", " and", " or", "|", "&"], line, lines)

@trace.debug("findlines")
def _parse(program):
    def _getlines(program):
        for line in enumerate(program.split("\n")):
            yield line
    instr = []
    lines = _getlines(program)
    try:
        while True:
            line = list(next(lines))
            line[1] = line[1].strip()
            if not line[1]:
                continue
            re_str = "^(?P<op>let |[\"'{{0-9]|{}|{})".format(_syntax["var"], 
                                                             _syntax["decl"])
            handlers = { "let " : _make_let, 
                         "exists ": _make_exists, 
                         "default": _make_comp }
            instr.append(grammar(re_str, line, lines, handlers))
    except StopIteration:
        pass
    return instr
    

@trace.info("findlines")
def run(program):
    return _parse(program)
    


if __name__ == "__main__":
    text = '''
    let x = { name == 'a',
              subnet == 'blah' }

    let f = { name == 'b' } ~> v
    
    f.bandwidth == 4000
    
    exists v and 
           { name == 'c' } ~> v or
           { name == 'd' } ~> { name == 'e' }

    '''
    
    print(run(text))
