from importlib import import_module

from .hill_climber import hill_climber
from .random_search import random_search
from .genetic_algorithm import genetic_algorithm
from .particle_swarm_optimisation import particle_swarm_optimisation

# public: HC, RS, GA

__all__ = [
    "hill_climber",
    "random_search",
    "genetic_algorithm",
    "particle_swarm_optimisation",
]

# Landscape-analysis tools need optional dependencies (numpy, matplotlib,
# scikit-gstat), so they are imported only on first access, e.g.
# `from pto.solvers import correlogram`. They are left out of __all__ so that
# `from pto.solvers import *` works without those dependencies.
_LAZY = {"correlogram", "correlogram_walks"}


def __getattr__(name):
    if name in _LAZY:
        return getattr(import_module(f".{name}", __name__), name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
