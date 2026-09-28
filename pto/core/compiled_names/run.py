import random
from .compiler import compile_generator
from ..automatic_names.autogens import rnd
from ..automatic_names.run import run as name_run


def run(Gen, *args, seed=None, **kwargs):
    """
    Run a solver on a problem, using compile-time name injection.

    This is a parallel layer to automatic_names/trans_run.py. Instead of
    generating trace names at runtime via stack inspection, it statically
    rewrites the generator's AST to inject name= keywords into every
    rnd.X() call. It uses the same rnd and tracer as automatic_names, so
    the generator is written in the same way (`from pto import rnd`).
    Usually selected with `run(..., naming="static")`.

    Parameters: same as automatic_names/trans_run.py (see its docstring).
    Names are always structured (name_type='str').
    """
    if seed is not None:
        rng_state = random.getstate()
        random.seed(seed)

    try:
        Gen = compile_generator(Gen, rnd)
        return name_run(Gen, *args, naming="static", **kwargs)
    finally:
        if seed is not None:
            random.setstate(rng_state)
