from flange.resolvers.settings import OPTIONS
from flange import config
from flange.tools import Block
from flange.tools.fact import FTreeNode, Entity, EntityType, Fact
from flange.version import __version__

import json, graphviz, logging

def create_facts(prefix, g, facts):
    results = []
    for fact in facts:
        match fact:
            case Fact(op, ref, target, value):
                if op == "app":
                    results.append(f"apply {value}")
                else:
                    match value:
                        case Block("flow", toks):
                            g.edge(f"{prefix}_{toks[0]}", f"{prefix}_{target}:p0", color="red")
                            g.edge(f"{prefix}_{target}:p1", f"{prefix}_{toks[1]}", color="red")
                        case _:
                            results.append(f"{target} {op} {value}")
            case _: pass
    return "|".join(results)

log = logging.getLogger("flange.resolver.dot")
def create_container(cname, g, node):
    with g.subgraph(name=f"cluster_{cname}") as container:
        for entity in node.entities:
            match entity:
                case Entity(quant, EntityType.NODE, name):
                    start = tag = f"{cname}_{name.val}"
                    facts = create_facts(cname, g, entity.facts)
                    record = f"{name.val.split('.')[0]}|{{ {facts} }}"
                    container.node(tag, record, shape='Mrecord', style='filled',
                                   fontcolor="red" if facts else "black")
                case Entity(quant, EntityType.FLOW, name):
                    start = tag = f"{cname}_{name.val}"
                    rname, facts = name.val.split('.')[0], create_facts(cname, g, entity.facts)
                    record = f"<p0>{rname}|{{ {facts} }}|<p1> "
                    container.node(tag, record, shape='record', fontcolor="red" if facts else "black")
        for i, child in enumerate(node.children):
            name = f"{cname}_{i}"
            end = create_container(name, g, child)
            g.edge(start, end, ltail=f"cluster_{cname}", lhead=f"cluster_{name}")
    return start

def run(program, env):
    dot = graphviz.Digraph(env.get('name', ''))
    dot.attr(compound='true')
    create_container("subgraph_0", dot, program)
    dot.view(cleanup=True)
    return str(dot.source)

if __name__ == "__main__":
    parser = config.parser_from_template(OPTIONS)
    conf = config.config_from_template(OPTIONS, "DOT resolver for .flog files", version=__version__)
    parser.add_argument("infile", type=str, help="Input filename")
    args = conf.from_parser(parser)
    if args["verbose"] > 1:
        conf.display(log)
    if not args["outfile"]: args["outfile"] = None

    with open(args["infile"], 'r') as f:
        dot = run(FTreeNode.deserialize(json.load(f)), {"name": args["infile"].split('.')[0]})
    if args["outfile"]:
        with open(args["outfile"], 'w') as f:
            f.write(dot)
    else:
        print(dot)
