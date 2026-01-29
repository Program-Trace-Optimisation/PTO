import random
from .compiler import compile_generator
from ..fine_distributions import run as fine_run


def run(Gen, *args, seed=None, **kwargs):
    """
    Run a solver on a problem, using compile-time name injection.

    This is a parallel layer to automatic_names/trans_run.py. Instead of
    generating trace names at runtime via stack inspection, it statically
    rewrites the generator's AST to inject name= keywords into every
    rnd.X() call before passing it to the fine_distributions layer.

    Parameters: same as automatic_names/trans_run.py (see its docstring).

    The name_type and dist_type parameters accepted by trans_run are not
    needed here: names are always structural (compiled from AST locations)
    and dist_type is forwarded to fine_distributions as-is.
    """
    if seed is not None:
        rng_state = random.getstate()
        random.seed(seed)

    Gen = compile_generator(Gen)
    result = fine_run(Gen, *args, **kwargs)

    if seed is not None:
        random.setstate(rng_state)

    return result
