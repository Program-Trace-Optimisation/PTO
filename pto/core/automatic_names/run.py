
from ..base import Op
from ..fine_distributions import run as fine_run

from .autoplay import tracer
from .autogens import rnd

def run(*args, name_type='str', dist_type='fine', **kwargs):
    """
    Configure naming and distribution types, then run optimization.
    
    Sets up the execution environment with specified naming and distribution
    strategies before delegating to the fine_run implementation.
    
    Args:
        *args: Positional arguments to pass to fine_run
        name_type: How to generate names - 'lin' (sequential) or 'str' (structural)
        dist_type: Type of distribution - 'coarse' or 'fine'
        **kwargs: Additional arguments to pass to fine_run
        
    Returns:
        Result from fine_run execution
        
    Example:
        # Run with structural naming and fine distributions
        solution = run(generator, fitness, name_type='str', dist_type='fine')
        
        # Run with sequential naming
        solution = run(generator, fitness, name_type='lin')
    """
    # Configure random number generator naming and distribution types
    rnd.CONFIG(name_type=name_type, dist_type=dist_type)
    
    # Bind autoplay tracer to operators
    Op.tracer = tracer
    
    # Run optimization with configured environment
    # Pass dist_type=None since already configured in rnd
    return fine_run(*args, dist_type=None, **kwargs)
