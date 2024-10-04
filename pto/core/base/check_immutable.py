
from functools import wraps

# DEBUG utility function

# decorator to check whether mutable input arguments of a function have been modified

def check_immutable(fun):
    
    @wraps(fun)
    def checked_fun(*args):
        
        before_args = repr(args)
        #print(before_args)
       
        out = fun(*args)
        
        after_args = repr(args)
        #print(after_args)
        
        assert before_args == after_args, "%s has modified inputs!" % fun.__name__
                
        return out
    
    return checked_fun
