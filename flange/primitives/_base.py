from unis import Runtime

class fl_type(type):
    def __new__(cls, name, bases, attrs, **kwargs):
        obj = super().__new__(cls, name, bases, attrs, **kwargs)
        obj.__fl_type__ = name
        return obj
        
    def __call__(cls, *args, **kwargs):
        obj = type.__call__(cls, *args, **kwargs)
        obj.__fl_init__(*args, **kwargs)
        return obj

class fl_object(metaclass=fl_type):
    def __new__(cls, *args, **kwargs):
        obj = super().__new__(cls)
        obj.__fl_type__ = "object"
        return obj
    
    def __fl_init__(self):
        pass
