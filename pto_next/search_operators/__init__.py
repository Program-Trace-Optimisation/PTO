"""Search operators: how whole solutions are varied and compared.

Each module of this package holds search operators, as plain functions:

    mutation   op(space, solution) -> Solution
    crossover  op(space, parent1, parent2) -> Solution   (or three parents)
    distance   op(space, solution1, solution2) -> float

and OPS, a tuple of them. An operator works on traces, using only the
search space (see space.py): space.play(trace) to turn a trace into a
solution, space.rng, and the variation of single decisions,
space.mutate_choice, space.crossover_choices, space.convex_crossover_choices,
space.distance_choices. It is selected by its function's name, eg
SearchSpace(..., mutation="mutate_point_ind"). Adding an operator is adding
a module here (or a function to one).

The names of the built-in operators are those of the original core, which
its solvers use.
"""

import importlib
import pkgutil

OPERATORS = {}


def _add(module):
    """Add the search operators of a module to OPERATORS."""
    for f in module.OPS:
        if f.__name__ in OPERATORS:
            raise ImportError(f"two search operator modules define {f.__name__}")
        OPERATORS[f.__name__] = f


for _module in sorted(m.name for m in pkgutil.iter_modules(__path__)):
    if not _module.startswith("_"):
        _add(importlib.import_module(f".{_module}", __name__))

__all__ = ["OPERATORS"]
