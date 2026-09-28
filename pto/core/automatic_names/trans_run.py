import random
from .run import run as name_run
from .gen import gen_fun


def run(Gen, *args, seed=None, **kwargs):
    """
    Run a solver, with structured names computed at run time (naming='dynamic').

    The generator's source is annotated (gen_fun) so that loops, comprehensions
    and nested functions push nodes on a naming stack, from which each rnd call
    gets its name. Parameters: see pto.core.interface.run, the user-facing run.
    """

    # Set random seed globally for the framework while preserving original state
    if seed is not None:
        rng_state = random.getstate()  # Save current state
        random.seed(seed)

    try:
        Gen = gen_fun(Gen)
        return name_run(Gen, *args, **kwargs)
    finally:
        # Restore random generator to previous state, also if the run raises
        if seed is not None:
            random.setstate(rng_state)


# FEATURES/LIMITATIONS (checked 2026-09):
#
# 1) To affect naming, functions called by the generator must be nested in the generator function
#    definition. Non-nested helpers still work, but their rnd calls get no call-site frame in
#    their names (silent).
#
# 2) generators cannot be defined as methods in classes, or as lambdas (error), since the
#    generator's source is re-parsed.
#
# (Earlier limitations no longer apply: generators can refer to global names, and rnd can be
#  used under another name, eg `from pto import rnd as random`.)


# Gen = gen(Gen, level=2, skipline=False)
# frame level 2 as gen used in nested name scope (not where Gen was defined)
# a more robust solution could be using global in the name space in the dfinition of gen?
# skipline false becuase we should not remove first line of source as gen is not used with decorator syntax (@gen)
