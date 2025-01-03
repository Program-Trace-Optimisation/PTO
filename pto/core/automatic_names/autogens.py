
from functools import wraps

from ..fine_distributions import RandomTraceable, supp

from .annotators import func_name, Name
from .autoplay import tracer

class AutoNamedRandomTraceable(RandomTraceable):
    """RandomTraceable that automatically generates names for random values."""
    
    NAME_GENERATORS = {
        'lin': Name.get_seq_name,
        'str': Name.get_stack_name
    }
    
    def __init__(self, name_type='str', **kwargs):
        super().__init__(**kwargs)
        self.name_type = None
        self.get_name = None
        self.CONFIG(name_type=name_type)
    
    def CONFIG(self, name_type=None, dist_type=None):
        """
        Configure naming and distribution types.
        If no arguments provided, returns current configuration.
        """
        if name_type is None and dist_type is None:
            return (self.dist_type, self.name_type)

        # Keep existing values if not specified
        dist_type = dist_type or self.dist_type
        name_type = name_type or self.name_type

        # Handle dist_type configuration
        if dist_type != self.dist_type:
            super().config(dist_type)
            
        # Handle name_type configuration
        if name_type != self.name_type:
            if name_type not in self.NAME_GENERATORS:
                raise ValueError(f"Invalid name_type: {name_type}. Must be one of {list(self.NAME_GENERATORS.keys())}")
            self.name_type = name_type
            self.get_name = self.NAME_GENERATORS[name_type]
            
        # Rebind functions with automatic naming
        self._bind_autonamed_functions()
        
        return (self.dist_type, self.name_type)
    
    def _bind_autonamed_functions(self):
        """Create autonamed versions of all supported random functions."""
        for fun in supp:
            base_func = getattr(self, fun.__name__)
            auto_func = self._add_autoname(base_func)
            setattr(self, fun.__name__, func_name(auto_func, args_name=False))
    
    def _add_autoname(self, func):
        """Wrap a function to use automatic naming if no name is provided."""
        @wraps(func)
        def wrapper(*args, name=None):
            return func(*args, name=name or self.get_name())
        return wrapper

rnd = AutoNamedRandomTraceable(tracer=tracer)
