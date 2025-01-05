
from functools import wraps

def check_immutable(fun):
    """
    A decorator that checks if a function modifies its mutable input arguments.
    
    This decorator compares the string representation of arguments before and after
    function execution to detect any modifications. It works with both positional
    and keyword arguments. The check can be disabled by running Python with the -O flag.
    
    Args:
        fun: The function to be decorated.
        
    Returns:
        wrapper: A wrapped function that checks input argument modification.
        If Python is run with -O flag, returns the original function unchanged.
        
    Raises:
        AssertionError: If any input argument is modified during function execution.
        
    Example:
        @check_immutable
        def append_to_list(lst, item):
            lst.append(item)  # This will raise AssertionError
            return lst
            
        @check_immutable
        def safe_extend(lst, item):
            return lst + [item]  # This will pass the check
    """
    if not __debug__:  # Will be True when running python with -O flag
        return fun
        
    @wraps(fun)
    def checked_fun(*args, **kwargs):
        before_args = repr(args)
        before_kwargs = repr(kwargs)
        
        out = fun(*args, **kwargs)
        
        after_args = repr(args)
        after_kwargs = repr(kwargs)
        
        assert before_args == after_args and before_kwargs == after_kwargs, \
            f"{fun.__name__} has modified inputs!"
                
        return out
    
    return checked_fun