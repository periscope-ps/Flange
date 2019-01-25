from unis.models.models import Primitive, List, Local, UnisObject, Context

def build_inline_topology(topo):
    resources, result = {}, {}
    def _visit(r, path, top=False):
        try:
            ty = r.getObject()
        except (NotImplementedError, AttributeError):
            ty, r = r, Context(r, None)
        if isinstance(ty, Primitive):
            return r._rt_raw
        elif isinstance(ty, List):
            return [_visit(nr, path + "/" + str(i)) for i,nr in enumerate(r)]
        elif isinstance(ty, Local):
            return {k:_visit(v, path+"/"+k) for k,v in r.items()}
        elif isinstance(ty, UnisObject):
            if r in resources and not top:
                return {"href": resources[r]}
            else:
                if r not in resources:
                    resources[r] = path
                return {k:_visit(v, path+"/"+k) for k,v in r.items()}
        else:
            return r
    for i, n in enumerate(topo.nodes):
        resources[n.getObject()] = "#/nodes/{}".format(i)
    for i, p in enumerate(topo.ports):
        resources[p.getObject()] = "#/ports/{}".format(i)
    for i, l in enumerate(topo.links):
        resources[l.getObject()] = "#/links/{}".format(i)
    result['nodes'] = [_visit(n, "#/nodes/{}".format(i), True) for i,n in enumerate(topo.nodes)]
    result['ports'] = [_visit(p, "#/ports/{}".format(i), True) for i,p in enumerate(topo.ports)]
    result['links'] = [_visit(l, "#/links/{}".format(i), True) for i,l in enumerate(topo.links)]

    return result
