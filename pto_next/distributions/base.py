"""Distribution: a kind of random decision, and how its values vary.

A distribution is an immutable value: its class and its parameters. It knows
how to sample a value, and how to vary values:

    mutate(value, rng)                          -> Choice
    crossover(value, other, rng)                -> Choice   (other: a Choice)
    convex_crossover(value, other1, other2, rng) -> Choice
    distance(value, other)                      -> float in [0, 1]
    repair(prev, rng)                           -> Choice   (prev: a Choice of
                                                   another distribution, carried over to this one)

The methods of this class are the generic, coarse behaviour, valid for any
distribution: resample, pick a parent, 0 or 1. A subclass overrides the ones
it can do better (fine behaviour), and falls back on these when the other
choice is of another kind (Distribution.crossover(self, ...)).
"""

from ..trace import Choice, decide  # noqa: F401  (decide: for the rnd functions)


class Distribution:
    __slots__ = ("params",)

    def __init__(self, *params):
        self.params = params

    def sample(self, rng):
        raise NotImplementedError

    def __eq__(self, other):
        return type(self) is type(other) and self.params == other.params

    __hash__ = None  # parameters may be unhashable (eg lists as options)

    def __repr__(self):
        return f"{type(self).__name__}{self.params!r}"

    def same_kind(self, *choices):
        """Whether the choices are of this class of distribution."""
        return all(type(c.dist) is type(self) for c in choices)

    # -- coarse behaviour ------------------------------------------------------------

    def mutate(self, value, rng):
        return Choice(self, self.sample(rng))

    def crossover(self, value, other, rng):
        return Choice(self, value) if rng.random() < 0.5 else other

    def convex_crossover(self, value, other1, other2, rng):
        return rng.choice((Choice(self, value), other1, other2))

    def distance(self, value, other):
        return 0.0 if self == other.dist and value == other.value else 1.0

    def repair(self, prev, rng):
        return Choice(self, self.sample(rng))


def frozen(seq):
    """An immutable copy of a sequence (ranges, tuples and strings as they are)."""
    return seq if isinstance(seq, (tuple, range, str)) else tuple(seq)
