class DependencyError(Exception):
    pass
class ResolutionError(Exception):
    pass
class CompilerError(Exception):
    def __init__(self, msg, token):
        self.token, self.msg = token, msg
        super().__init__()
class FlangeSyntaxError(CompilerError):
    ty = "SyntaxError"
