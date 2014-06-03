from copy import deepcopy

class ObservableSet(set):
    def __init__(self, s=()):
        super(ObservableSet,self).__init__(s)
        self._observers = set()
    
    def register(self, observer):
        self._observers.add(observer)
    
    def unregister(self, observer):
        self._observers.discard(observer)
    
    def notify(self):
        for observer in self._observers:
            observer.update(self)

    @classmethod
    def _wrap_methods(cls, names):
        def wrap_method_closure(name):
            def inner(self, *args):
                old = ObservableSet(self)
                result = getattr(super(cls, self), name)(*args)
                if isinstance(result, set):
                    result = cls(result)
                if old != self:
                    self.notify()
                return result
            inner.fn_name = name
            setattr(cls, name, inner)
        for name in names:
            wrap_method_closure(name)

ObservableSet._wrap_methods(['__ror__', 'difference_update', '__isub__', 
    'symmetric_difference', '__rsub__', '__and__', '__rand__', 'intersection',
    'difference', '__iand__', 'union', '__ixor__', 
    'symmetric_difference_update', '__or__', 'copy', '__rxor__',
    'intersection_update', '__xor__', '__ior__', '__sub__', 'add', 'remove',
    'clear'
])


class AttrDict(dict):
    """
    A dictionary where keys can be accessed as attributes.
    
    """
    
    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self
    
    def __deepcopy__(self, memo):
        return AttrDict(deepcopy(dict(self)))
    
    def override(self, other):
        """
        Override the values of other with this dictionary; every key-value pair
        of other is added to this dictionary, overriding the current value if
        necessary.
        
        """
        for k, v in other.items():
            self[k] = v