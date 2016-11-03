from . import FlangeTree

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
