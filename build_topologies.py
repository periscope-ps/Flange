from unis.models import *
from unis.runtime import Runtime
from unis.rest import UnisReferenceError
from unis.models.lists import UnisCollection
import itertools



def commit(target):
    collections = ["ports", "nodes", "links", "paths", "networks", 
                   "domains", "topologies", "exnodes", "extents"]
    unordered = filter(lambda x: x not in collections, target.collections)
    collections.extend(unordered)
    for collection in collections:
        for item in getattr(target, collection):
            item.commit()



def node(rt, name):
    node = Node({"name": name})
    rt.insert(node)
    return node

def port(rt, node):
    port = Port({"name": ":".join([node.name, "port1"])})
    rt.insert(port)
    node.ports = [port]
    return port

def link(rt, mapping):
    left = next(rt.ports.where({"name": ":".join([mapping[0], "port1"])}))
    right = next(rt.ports.where({"name": ":".join([mapping[1], "port1"])}))
    link = Link({"name": "--".join([left.name, right.name]), 
                 "directed": False, 
                 "endpoints": [left, right]})
    rt.insert(link)
    return link
    
def domain(rt, name):
    nodes = list(rt.nodes.where(lambda x: x.name == name))
    ports = list(rt.ports.where(lambda x: x.name.startswith(name)))
    links = list(rt.links.where(lambda x: x.endpoints[0].name.startswith(name)))
    domain = Domain({"name": name, "nodes": nodes, "ports": ports, "links":links})
    rt.insert(domain)
    return domain

def topology(rt, name, ports, nodes, links, domains):
    topo = Topology({"name": name, "ports": ports, 
                     "nodes": nodes, "links": links, 
                     "domains": domains})
    rt.insert(topo)



def osiris(url):
    with Runtime(url) as rt:
        domain_names = ["IU", "WSU", "MSU", "CHIC", "SALT", 
                        "SC16", "IU-Crest", "UMich", "Cloudlab"]
        link_map = [("IU", "CHIC"), ("UMich", "CHIC"), ("WSU", "CHIC"), 
                    ("MSU", "CHIC"), ("CHIC", "SALT"), ("Cloudlab", "SALT"), 
                    ("SC16", "SALT"), ("SC16", "UMich"), ("SC16", "IU-Crest")]
        nodes = [node(rt, d) for d in domain_names]
        ports = [port(rt, n) for n in nodes]
        links = [link(rt, l) for l in link_map]
        domains = [domain(rt, d) for d in domain_names]
        topology(rt, "OSiRIS", nodes, ports, links, domains)
        commit(rt)



def ring_spur(url, ring, spurs):
    def name(link, spur): return "Node-{0}-{1}".format(link, spur)
    
    node_names = [name(i, j)
                  for j in range(spurs)
                  for i in range(ring)]
    ring_links = [(name(i,0), name((i+1)%ring, 0))
                  for i in range(ring)]
    spur_links = [(name(i,j), name(i, 0))
                  for j in range(1, spurs)
                  for i in range(ring)]
    
    link_map = list(itertools.chain(ring_links, spur_links))

    with Runtime(url) as rt:
        nodes = [node(rt, d) for d in node_names]
        ports = [port(rt, n) for n in nodes]
        links = [link(rt, l) for l in link_map]
        domain = Domain({"name": "ring-domain", "nodes": nodes, "ports": ports, "links": links})
        rt.insert(domain)
        topology(rt, "ring", nodes, ports, [], [domain])
        commit(rt)
        



def main():
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description="Topology builder for test topologies in UNIS")
    parser.add_argument('unis', 
                        help="Address of the UNIS to connect to (must include http://)")
    parser.add_argument('-t', '--topology', choices=["all", "osiris", "ring"], default="osiris", required=False,
                        help="Topology name to build.")
    parser.add_argument('-r', "--ring", default=10, type=int,
                        help="Circumferernce of a ring to build (for ring only)")
    parser.add_argument('-s', "--spur", default=3, type=int,
                        help="Length of spurs to build (for ring only)")

    args = parser.parse_args(sys.argv[1:])
    
    if args.topology == "osiris" or args.topology == "all":
        print("Building osiris")
        osiris(args.unis)
        print("Done!\n")
        
    if args.topology == "ring" or args.topology == "all":
        print("Building ring/spur with {0} circumference and spurs of length {1}".format(args.ring, args.spur))
        ring_spur(args.unis, args.ring, args.spur)
        print("Done!\n")
    
    
if __name__ == "__main__": 
    main()

