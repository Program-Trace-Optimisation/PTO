
from functools import wraps

from ..base import Dist, tracer

from .supp import supp
from .distributions import Random_real, Random_int, Random_cat

class RandomTraceable:
    """Creates traceable versions of random functions."""
    
    DISTRIBUTION_TYPES = ['coarse', 'fine']
    CLASS_MAP = {'real': Random_real, 'int': Random_int, 'cat': Random_cat}
        
    def __init__(self, dist_type='fine', tracer=tracer):
        self.tracer = tracer         
        self.dist_type = None  
        self.config(dist_type)

    def config(self, dist_type=None):
        """Configure or get the distribution type."""
        if dist_type is None:
            return self.dist_type

        if dist_type not in self.DISTRIBUTION_TYPES:
            raise ValueError(f"Invalid dist_type: {dist_type}. Must be one of {self.DISTRIBUTION_TYPES}")

        self.dist_type = dist_type
        self._bind_traceable_functions()

    def _bind_traceable_functions(self):
        """Bind traceable versions of all supported random functions."""
        for fun in supp:
            dist_cls = Dist if self.dist_type == 'coarse' else self.CLASS_MAP[supp[fun][0]]        
            setattr(self, fun.__name__, self._create_traceable(fun, dist_cls))   

    def _create_traceable(self, fun, dist_cls):
        """Create a traceable version of a random function."""
        @wraps(fun)
        def traceable(*args, name=None):
            return self.tracer.sample(name, dist_cls(fun, *args))
        return traceable

rnd = RandomTraceable()
