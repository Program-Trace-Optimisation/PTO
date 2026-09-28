"""The search space: a problem bound to how its solutions are represented and varied.

A SearchSpace binds a generator and a fitness function to a naming, to fine
or coarse variation of the decisions, to two random number generators, and to
the search operators chosen for mutation and crossover. It is what solvers
see: they create, evaluate, mutate and recombine solutions through it and
never see what a solution looks like. It implements no operators itself:
the search operators are in search_operators/, and each distribution knows
how its decisions vary (distributions/).

Every search operator is also available as a method under its own name (eg
space.mutate_point_ind), which is how the solvers of the original core choose
them.

Randomness comes from two independent streams, derived by name from the seed:

    decision_rng  the generator's randomness: the decisions sampled or repaired
                  while playing a trace. The only randomness that traces record.
    search_rng    the search's randomness: search operators and solvers draw
                  their random numbers from it. Never recorded.

So the search draws no numbers from the generator's stream: with the same seed,
the initial solutions are the same whatever the operators and solver. The
global random module is left to the user (problem data, noisy fitness, and rnd
outside a play).
"""

import random
import types
from typing import Any, NamedTuple

from .distributions import Distribution
from .naming import NAMINGS
from .search_operators import OPERATORS
from .trace import play

VARIATIONS = ("fine", "coarse")


class Solution(NamedTuple):
    pheno: Any  # what the generator returned
    geno: dict  # the trace: address -> Choice


class SearchSpace:
    def __init__(
        self,
        generator,
        fitness,
        gen_args=(),
        fit_args=(),
        *,
        naming="dynamic",
        operators="fine",
        mutation="mutate_point_ind",
        crossover="crossover_uniform_ind",
        seed=None,
    ):
        """
        naming:    'dynamic' (default), 'static' or 'linear' (see naming.py)
        operators: 'fine' (default) or 'coarse' variation of the decisions
        mutation, crossover: names of the search operators used as
                   mutate_ind and crossover_ind (see search_operators/)
        seed:      seed of this space's random streams (decision_rng, search_rng)
        """
        if naming not in NAMINGS:
            raise ValueError(f"Invalid naming: {naming!r}. Must be one of {list(NAMINGS)}")
        if operators not in VARIATIONS:
            raise ValueError(f"Invalid operators: {operators!r}. Must be one of {list(VARIATIONS)}")
        self.naming = NAMINGS[naming]()
        self.fine = operators == "fine"
        self.generator = self.naming.prepare(generator)
        self.gen_args = tuple(gen_args)
        self.fitness = fitness
        self.fit_args = tuple(fit_args)
        self.decision_rng = _stream(seed, "decisions")
        self.search_rng = _stream(seed, "search")
        self.mutate_ind = getattr(self, mutation)
        self.crossover_ind = getattr(self, crossover)

    def __getattr__(self, name):
        """A search operator, as a method of this space."""
        if name in OPERATORS:
            method = types.MethodType(OPERATORS[name], self)
            setattr(self, name, method)
            return method
        raise AttributeError(f"{type(self).__name__!r} has no attribute or search operator {name!r}")

    def __repr__(self):
        return (f"SearchSpace({self.generator.__name__}, {getattr(self.fitness, '__name__', self.fitness)}, "
                f"naming={type(self.naming).__name__.lower()}, operators={'fine' if self.fine else 'coarse'})")

    # -- solutions ---------------------------------------------------------------

    def play(self, trace):
        """The solution the generator makes from trace (repairing it as needed)."""
        pheno, geno = play(self.generator, trace, self.decision_rng, self.repair_choice,
                           self.naming.start(), self.gen_args)
        return Solution(pheno, geno)

    def create_ind(self):
        return self.play({})

    fix_ind = play

    def evaluate_ind(self, sol):
        return self.fitness(sol.pheno, *self.fit_args)

    # -- variation of single decisions: the distribution's own (fine) or coarse --

    def _variation(self, dist):
        return type(dist) if self.fine else Distribution

    def mutate_choice(self, c):
        return self._variation(c.dist).mutate(c.dist, c.value, self.search_rng)

    def crossover_choices(self, c1, c2):
        return self._variation(c1.dist).crossover(c1.dist, c1.value, c2, self.search_rng)

    def convex_crossover_choices(self, c1, c2, c3):
        return self._variation(c1.dist).convex_crossover(c1.dist, c1.value, c2, c3, self.search_rng)

    def distance_choices(self, c1, c2):
        return self._variation(c1.dist).distance(c1.dist, c1.value, c2)

    def repair_choice(self, prev, dist, rng):  # called by play, with decision_rng
        return self._variation(dist).repair(dist, prev, rng)


def _stream(seed, name):
    """A random number generator for one purpose: seeded from seed and name, so that
    streams are independent and the same in every process; unseeded if seed is None."""
    return random.Random() if seed is None else random.Random(f"{seed}:{name}")
