from unis import Runtime

class fl_type(type):
    def __new__(cls, name, bases, attrs, **kwargs):
        obj = super().__new__(cls, name, bases, attrs, **kwargs)
        obj.__fl_type__ = name
        return obj
        
class fl_object(metaclass=fl_type):
    pass
