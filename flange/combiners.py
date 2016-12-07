from ._internal import autotree
"""
Combiners take a set of results and put them together into a single result.
Combiners return the result graph if the succeed OR a CombinerException if
  there is a problem with one or more rules.  The CombinerException includes
  any rules that were not run.  It may include a partially transformed graph.
"""
class CombinerFailure(RuntimeError):
    """A combiner did not succeed. The unexecuted rules and partially modified graph
    are returned here."""
    def __init__(self, rules):
        super()
        self.rules = rules
        self.graph = graph


@autotree("merge", "*rules")
def fair_merge(self, graph): 
    raise Exception("NOT IMPLEMENTED")


@autotree("*rules")
def priority(self, graph): 
   """Execute rules in order, passing the result of the first to the second, etc.  
   Stop after first failure."""

   for (i, rule) in enumerate(self.rules):
       try:
           graph = rule(graph)
       except:
           raise CombinerFailure(self.rules[:i], graph)

   return graph


@autotree("weight", "*rules")
def best(self, graph):
    """
    Execute each rules on the original input graph.  
    Keep the one that produces a result with the highest score by the weight function.

    TODO: Communicate which rule was used?
    """

    def swallow(rule):
        try:
            return rule(graph)
        except:
            return None

    options = [swallow(rule) for rule in self.rules]
    options = filter(lambda x: x is not None, options)

    weights = [self.weight(option) for option in options]
    max_at = weights.index(max(weights))
    return options[max_at]


@autotree("*rules", return_fails=False)
def best_effort(self, graph):
    """
    Attempt to run each rule, passing the result of the first to the second. 
    If a rule fails, it is skipped and the next one is attempted.

    return_fails (False) -- If true, returns a pair (graph, failing rules)
    """

    fails = []
    for rule in rules:
        try:
            graph = rule(graph)
        except:
            fails.append(rule)

    if return_fails and len(fails) > 0: 
        return (graph, fails)
    else:
        return graph

@autotree("*rules")
def all(self, graph): 
    """Execute rules in order, passing the result of the first to the second, etc.
    Only succeed if all rules succeed."""

    try:
        return priority(self.rules)(graph)
    except:
        raise CombinerFailure(rules, graph)


@autotree("*rules", weight=None)
def permutations(self, graph): 
    """
    Try rules in a given order.  If they don't all pass, try a new order.
    Tries them using 'all'.  
    
    If weight is supplied, tries all permutations and returns the best-weighted one.
    If weight is not supplied, returns the first order that completes all rules.
    """

    options = []
    for order in itertools.permutations(self.rules):
        try:
            options.append(all(order)(graph))
            if not self.weight: return results[0]
        except:
            pass

    if len(results) == 0: raise CombinerFailure(self.rules, graph)

    weights = [self.weight(option) for option in options]
    max_at = weights.index(max(weights))
    return options[max_at]
   

