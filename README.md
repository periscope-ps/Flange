# General Things TODO

* Add ID to rule instances so the effects of a rule can be tracked.  
  Then if a rule is canceled, effects can be removed.  
  If the rule is dynamic, its prior effects can be removed if needed.

* Subscribe to UNIS updates in the runtime, re-run monitors when changes occur
* Graph transformation functions

# General ideas

* Graphs are made of vertexes and edges
* Netoworks are made of nodes and links
* A network path/route is a set of link-verticies that share an common path attribute,
  adding paths is just adding attributes (but working with them may require reifying 
  them asa edges in the graph)
