class FlangeTree(object):
    """
    Deferred/curried function as an object.
    
    The most common pattern is to pass a number of arguments at construction, 
    and later invoke the whole function on a graph.
    """

    def __call__(self, graph):
        "Process the passed graph"
        raise RuntimeError("Must override the call method")

    def focus(self, graph):
        """What part of the graph is of interest to this rule.
        Should correspond to a partial evaluation of the call, 
        but not compute the end result, just the portion of interest

        Default implementation is a call to the regular "__call__" method,
        since that should be stateless...
        """
        return [self(graph)]

    def __rshift__(self, other):
        "Chaining operator.  Calls self, then passes result to call of other"
        return lambda arg: other(self(arg))

def autotree(*passed_args, **passed_kwargs):
    """
    Create a decorator that makes a FlangTree subclass from a function.
    The resulting class will have same name as the source function.
    The source function is used umodified, but its exectution context
    will be as a member of a class. It should therefore probably have 'self' 
    as its first argument.

    *passed_args -- Names of required arguments to the generated 
                    class constructor
    **passed_kwargs -- Names and default values for optional arguments to 
                    the generated class constructor

    Note: There is no way to do *args or **kwargs at this time.
    """

    def build_class(call, name, passed_args, passed_kwargs):
        def init(self, *args, **kwargs):
            for (name, arg) in zip(passed_args, args):
                self.__dict__[name] = arg

            # Handle *args
            if len(args) > len(passed_args) \
                 and len(passed_args) > 0 \
                 and passed_args[-1].beginswith("*") \
                 and not passed_args[-1].beginswith("**"):
                     self.__dict__[name[1:]] = args[len(passed_args):]

            for (name, val) in passed_kwargs.items():
                self.__dict__[name] = val

            for (name, val) in kwargs.items():
                try:
                    passed_kwargs[name]   #Raise exception if name not defined at decorator
                    self.__dict__[name] = val
                except:
                    raise Exception("Unknown keyword argument passed: {0}".format(name))

        body_dict = {"__init__": init,
                     "__call__": call}

        cls = type(name, (FlangeTree,), body_dict)
        return cls
    
    def decorator(fn):
        return build_class(fn, fn.__name__, passed_args, passed_kwargs)
    
    return decorator
