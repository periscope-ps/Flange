__all__ = ["actions", "combiners", "conditions", "graphs", "locations", "roots", "runtime", "utils"]

from .actions import *
from .combiners import *
from .conditions import *
from .graphs import *
from .locations import *
from .roots import *
from .runtime import *
from .utils import *

# Flange uses vertex/edge to refer to graph items and node/link to refer to network things.
# So we monkey patch in a vertices-named methods for all the graph classes
# Patching here seems to work when importing any flange modules...
# and any subsequent use of networkx by any module.
# This might not be good form, and it might be mildly dangerous, since
# these methods could theoretically be overwritten subsequently by other module imports.
# Live (slightly) dangerously
import networkx as nx

def get_vertex_attr(self, item):
    if item == "vertex": return self.node
    raise AttributeError(item)

nx.classes.Graph.vertices = lambda self: self.nodes()
nx.classes.Graph.vertices_iter = lambda self: self.nodes_iter()
nx.classes.Graph.has_vertex = lambda self, vertex: self.has_node(vertex)
nx.classes.Graph.number_of_vertices = lambda self: self.number_of_nodes()
nx.classes.Graph.vertices_with_self_loops = lambda self: self.nodes_with_self_loops()
nx.classes.Graph.add_vertex = lambda self, *args, **kwargs: self.add_node(*args, **kwargs)
nx.classes.Graph.add_vertices_from = lambda self, iterable: self.add_nodes_from(iterable)
nx.classes.Graph.__getattr__ = get_vertex_attr

nx.get_vertex_attributes = lambda g, name: nx.get_node_attributes(g, name)
nx.set_vertex_attributes = lambda g, name, vals: nx.set_node_attributes(g, name, vals)
