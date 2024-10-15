
from functools import wraps

from ..base import Dist, tracer

from .supp import supp
from .distributions import Random_real, Random_int, Random_cat

class RandomTraceable:
    """
    Container for traceable random functions.
    """
        
    def __init__(self, dist_type='repair', tracer=tracer):
        # bind rnd to tracer
        self.tracer = tracer 

        # map parameters and classes
        self.cls_map = {
            'coarse': {'real': Dist,               'int': Dist,              'cat': Dist},
            'fine':   {'real': Random_real,        'int': Random_int,        'cat': Random_cat}
        }
        
        self.dist_type = None  # Initialize dist_type
        self.config(dist_type)  # Set up the configuration

    def config(self, dist_type=None):
        
        # read config
        if dist_type is None:
            return self.dist_type

        # validate dist_type
        if dist_type not in self.cls_map:
            raise ValueError(f"Invalid dist_type: {dist_type}. Must be one of {list(self.cls_map.keys())}")

        # store config mode
        self.dist_type = dist_type
    
        # create traceable functions
        for fun in supp:
            setattr(self, fun.__name__, self._make_traceable(fun)) 

    def _make_traceable(self, fun):
        # get function's class
        dist_cls = self.cls_map[self.dist_type][supp[fun][0]]        

        @wraps(fun)
        def traceable(*args, name=None):
            return self.tracer.sample(name, dist_cls(fun, *args))
    
        return traceable

# Create an instance of RandomTraceable
rnd = RandomTraceable()
