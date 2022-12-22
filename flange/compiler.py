import logging, json

from flange.settings import OPTIONS
from flange import passes, config
from flange.exceptions import CompilerError
from flange.version import __version__

from pprint import pprint

log = logging.getLogger("flange")
def _print_exp(filename, program, exp):
    if hasattr(exp.token, "tokens"):
        return _print_exp(filename, program, type(exp)(exp.msg, exp.token.tokens[0]))
    line = program.split("\n")[exp.token.lineno]
    pad = f"   {' ' * len(filename)} {' ' * len(str(exp.token.lineno))}    {' ' * exp.token.charno}"
    print(f"  [{filename}:{exp.token.lineno}] - {line}")
    print(f"{pad}^")
    print(f"{pad}{exp.ty} {exp.msg}")
    exit(-1)

def flange(program, env=None):
    try:
        v = passes.run(program, env or [])
        return v
    except CompilerError as exp:
        _print_exp("<stdin>", program, exp)

def debug(program, env=None):
    try:
        return passes.run(program, env or [], debug=True)
    except CompilerError as exp:
        _print_exp("<stdin>", program, exp)

def main():
    parser = config.parser_from_template(OPTIONS)
    conf = config.config_from_template(OPTIONS,"Flange NOS language compiler",  version=__version__)
    parser.add_argument("infile", nargs='?', type=str, help="Input filename [default: stdin]")
    args = conf.from_parser(parser)
    if args["verbose"] > 1:
        conf.display(log)
    
    if args.get("infile", None):
        with open(args["infile"], 'r') as f:
            program = f.read()
    else:
        program, l = "", input()
        while l:
            program += l.expandtabs(4) + "\n"
            l = input()

    
    result = debug(program) if args["verbose"] else flange(program)
    if args["outfile"]:
        with open(args["outfile"], 'w') as f:
            json.dump(result.serialize(), f)
    else:
        print(json.dumps(result.serialize(), indent=2))
