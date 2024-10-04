
from functools import wraps

from ..fine_distributions import RandomTraceable, supp

from .annotators import func_name, Name
from .autoplay import tracer

class AutoNamedRandomTraceable(RandomTraceable):
    def __init__(self, name_type = 'str', **kwargs):
        super().__init__(**kwargs)

        self.name_type = None  # Initialize name_type
        self.CONFIG(name_type=name_type)  # Set up the configuration

    def CONFIG(self, name_type=None, dist_type=None):
        # CONFIG (uppercase) is the function to export and use
        # FIXME more explanation needed here

        # read config
        if name_type is None and dist_type is None: 
            return (self.dist_type, self.name_type)

        # new config
        dist_type = dist_type or self.dist_type
        name_type = name_type or self.name_type

        # apply dist_type
        super().config(dist_type)
                    
        # validate name_type
        if name_type not in ['lin','str']:
            raise ValueError(f"Invalid name_type: {name_type}. Must be one of {['lin','str']}")

        # store config mode
        self.name_type = name_type

        # select name function
        self.get_name = {'lin' : Name.get_seq_name, 'str' : Name.get_stack_name}[self.name_type] 
    
        # create autonamed functions
        for fun in supp:
            func = self._use_name(getattr(self, fun.__name__))
            setattr(self, fun.__name__, func_name(func, args_name=False))

        # return current config
        return (self.dist_type, self.name_type)

    def _use_name(self, func):

        @wraps(func)
        def use_name_func(*args, name=None):
            name=name or self.get_name()
            # print(name)
            return func(*args, name=name)

        return use_name_func

# Create an instance of AutoNamedRandomTraceable
rnd = AutoNamedRandomTraceable(tracer = tracer) # binds to autoplay tracer

