"""Distributions: the kinds of random decision, and rnd.

Each module of this package is one family of distributions, complete:

  * the distribution classes: subclasses of base.Distribution, each an
    immutable value (its class and parameters) that knows how to sample a
    value, and overrides whichever variation methods it can do better than
    the coarse ones of Distribution (mutate, crossover, convex_crossover,
    distance, repair);
  * the rnd functions that make them: functions with the signature of their
    counterpart in the random module plus a keyword `name=None`, each making
    its decision with base.decide(distribution, name);
  * RND, a tuple of those rnd functions.

rnd has the rnd functions of all the modules: adding a distribution is adding
a module here. Families: real (random, uniform, gauss, ...), integer
(randrange, randint), categorical (choice), sequences (shuffle, sample,
choices).
"""

import importlib
import pkgutil

from .base import Distribution


class Rnd:
    """A drop-in for the random module whose calls are random decisions:
    recorded during a play (see trace.py), plain random numbers otherwise.
    Every function takes an optional keyword `name`, the decision's address;
    the naming fills it in when it is omitted."""

    def __repr__(self):
        return f"<rnd: {', '.join(sorted(vars(self)))}>"


rnd = Rnd()


def _add(module):
    """Add the rnd functions of a distribution module to rnd."""
    for f in module.RND:
        if hasattr(rnd, f.__name__):
            raise ImportError(f"two distribution modules define rnd.{f.__name__}")
        setattr(rnd, f.__name__, f)


for _module in sorted(m.name for m in pkgutil.iter_modules(__path__)):
    if _module != "base" and not _module.startswith("_"):
        _add(importlib.import_module(f".{_module}", __name__))

__all__ = ["Distribution", "Rnd", "rnd"]
