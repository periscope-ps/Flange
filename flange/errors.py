class ActionFailureError(RuntimeError):
    "Inidicates rule action was taken BUT the test of that rule still fails"
    pass

class NoValidChoice(RuntimeError):
    "Indicates that a search returned zero valid options."
    pass

class NoChange(RuntimeError):
    "Indicates that nothing needs to be done to a graph."
    pass

