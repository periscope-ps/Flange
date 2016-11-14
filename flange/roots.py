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

    def __call__(self, *args):
        rslt=args
        if not self.test(*args):
            rslt = self.action(*args)
            if not self.test(*rslt):
                raise ActionFailureError()
            return rslt
        return rslt

class assure(FlangeTree):
    """ 
    Encapsualtes a common exists/place pattern for rules

    assure(property, selector, graph) ==> 
       rule(exists(property, selector, graph), 
            place(property, selector graph)) 
    """

    def __init__(self, property, selector, graph):
        self.rule = rule(conditions.exists(property, selector, graph), 
                         actions.place(property, selector, graph))

    def __call__(self, *args):
        return self.rule(*args)



class switch(FlangeTree):
    "A rule that always tests to True."
    def default(action): return rule(lambda *x: True, action)

    "Tests rules in order. Does the action associated with the first item test that passes."
    def __init__(self, *rules):
        self.rules = rules

    def __call__(self):
        for rule in self.rules:
            if rule.test():
                return rule.action()
        raise NoValidChoice("No action take in switch")


class group(FlangeTree):
    """
    Given a single graph, perform several actions.
    Actions are evaluated independantly on the graph, then the combiner determines the final result.

    Combiners include fair-flow or best-of.
    """

    def __init__(self, combiner, *actions):
        self.combiner = combiner
        self.actions = actions

    def call(self, graph):
        result = []
        for actions in action:
            result.push(action(graph))

        return combiner(*result)

class monitor(FlangeTree):
    """Rule prefixed by some gate conditions.  
    The idea is the gate conditions capture wether or not a new result is even possible.
    
    In the long run-this class should be *automatically* constructed if dynamic
    conditions are present in a rule.
    
    If re-execution is needed, returns the result of rule.
    If re-execution is not needs, raises NoChange.

    TODO: take a graph as the argument to "call"; pass the graph ***instance*** into the gate and the rule

    TODO: Make a variant that is a callback on data change instead of polling-based 'retry' based
    TODO: Integrate with rule so it automatically creates this IF there is some dyanmic statement
    """

    def __init__(self, root, gate=lambda: True):
        self.root = root
        self.gate = gate
        self.prior = None

    def retry(self):
        condition = self.gate()
        if condition == self.prior:
            self.prior = condition
            return False 
        else:
            self.prior = condition
            return True 

    def __call__(self):
        if self.retry(): return self.root()
        else: raise NoChange()
