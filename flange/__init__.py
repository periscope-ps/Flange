__all__ = ["locations", "graphs", "conditions", "errors", "actions"]
from .locations import *
from .graphs import *
from .conditions import *
from .roots import *
from .actions import *


import networkx as nx
# Flange uses vertex/edge to refer to graph items and node/link to refer to network things.
# So we monkey patch in a vertices-named methods for all the graph classes
# Patching here seems to work when importing any flange modules...
# and any subsequent use of networkx by any module.
# This might not be good form, and it might be mildly dangerous, since
# these methods could theoretically be overwitten subsequently by other module imports.
# Live (slightly) dangerously

nx.classes.Graph.vertices = lambda self: self.nodes()
nx.classes.Graph.vertices_iter = lambda self: self.nodes_iter()
nx.classes.Graph.has_vertex = lambda self, vertex: self.has_node(vertex)
nx.classes.Graph.number_of_vertices = lambda self: self.number_of_nodes()
nx.classes.Graph.vertices_with_self_loops = lambda self: self.nodes_with_self_loops()
nx.classes.Graph.add_vertex = lambda self, vertex: self.add_node(vertex)
nx.classes.Graph.add_vertices_from = lambda self, iterable: self.add_nodes_from(iterable)
