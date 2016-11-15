from ._internal import FlangeTree
from .errors import ActionFailureError, NoValidChoice, NoChange
from . import actions 
from . import conditions


class rule(FlangeTree):
    """
    A test/action pair. Executes the action if the rule fails.
    Returns the result of action (if taken) or the original arguments (if no action taken).

    The result of the action must be a list of things of the same type as the args.
    This makes the test/action/retest work properly.
    """

    def __init__(self, test, action):
        self.test = test
        self.action = action
    
    def __call__(self, graph):
        rslt=graph
        if not self.test(graph):
            rslt = self.action(graph)
            if not self.test(rslt):
                raise ActionFailureError()
            return rslt
        return rslt

    def focus(self, graph):
        try : test = self.test.focus(graph)
        except: test = self.test(graph)

        try: action = self.action.focus(graph)
        except: action = self.action(graph)

        return (test, action)

class assure(FlangeTree):
    """ 
    Encapsualtes a common exists/place pattern for rules

    assure(property, selector, graph) ==> 
       rule(exists(property, selector, graph), 
            place(property, selector graph)) 
    """

    def __init__(self, property, selector):
        self.rule = rule(conditions.exists(property, selector), 
                         actions.place(property, selector))

    def __call__(self, *args):
        return self.rule(*args)

    def focus(self, graph): return self.rule.focus(graph)


class switch(FlangeTree):
    "A rule that always tests to True."
    def default(action): return rule(lambda *x: True, action)

    "Tests rules in order. Does the action associated with the first item test that passes."
    def __init__(self, *rules):
        self.rules = rules

    def __call__(self, graph):
        for rule in self.rules:
            if rule.test(graph):
                return rule.action(graph)
        raise NoValidChoice("No action take in switch")
    
    def focus(self, graph): 
        return [rule.focus(graph) for rule in self.rules]


class group(FlangeTree):
    """
    Given a single graph, perform several actions.
    Actions are evaluated independantly on the graph, then the combiner determines the final result.

    Combiners include fair-flow or best-of.
    """

    def __init__(self, combiner, *actions):
        self.combiner = combiner
        self.actions = actions

    def __call__(self, graph):
        result = []
        for actions in action:
            result.push(action(graph))

        return combiner(*result)

    def focus(self, graph):
        return [action.focus(graph) for action in self.actions]

class monitor(FlangeTree):
    """Rule prefixed by some gate conditions.  
    The idea is the gate conditions capture wether or not a new result is even possible.
    
    In the long run-this class should be *automatically* constructed if dynamic
    conditions are present in a rule.
    
    If re-execution is needed, returns the result of rule.
    If re-execution is not needs, raises NoChange.

    TODO: Gate is a Flange-tree, so 'focus' will return on gate.
    TODO: Make a variant that is a callback on data change instead of polling-based 'retry' based
    TODO: Integrate with rule so it automatically creates this IF there is some dyanmic statement
    """

    def __init__(self, root, gate=lambda g: True):
        self.root = root
        self.gate = gate
        self.prior = None
    
    def __call__(self, graph):
        if self.retry(graph): return self.root(graph)
        else: raise NoChange()

    def retry(self, graph):
        condition = self.gate(graph)
        if condition == self.prior:
            self.prior = condition
            return False 
        else:
            self.prior = condition
            return True 


    def focus(self, graph):
        return (self.gate.focus(graph),  self.root.focus(graph))
