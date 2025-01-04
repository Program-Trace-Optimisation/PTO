
from functools import wraps

from ..base import Dist, tracer

from .supp import rng_specs
from .distributions import Random_real, Random_int, Random_cat, Random_seq

class RandomTraceable:
    """Creates traceable versions of random functions."""
    
    DISTRIBUTION_TYPES = ['coarse', 'fine']
    CLASS_MAP = {'real': Random_real, 'int': Random_int, 'cat': Random_cat, 'seq': Random_seq}
        
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
        for fun in rng_specs:
            dist_cls = Dist if self.dist_type == 'coarse' else self.CLASS_MAP[rng_specs[fun].type]        
            setattr(self, fun.__name__, self._create_traceable(fun, dist_cls))   

    def _create_traceable(self, fun, dist_cls):
        """Create a traceable version of a random function."""
        
        # handle specially inplace input for shuffle 
        if fun.__name__ == 'shuffle':
            def shuffle(seq, name=None):
                seq[:] = self.tracer.sample(name, dist_cls(fun, seq))
            return shuffle

        @wraps(fun)
        def traceable(*args, name=None):
            return self.tracer.sample(name, dist_cls(fun, *args))
        
        return traceable

rnd = RandomTraceable()
