from ._internal import FlangeTree
from .errors import ActionFailureError, NoValidChoice
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
