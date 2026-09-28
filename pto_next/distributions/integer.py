"""Integer-valued decisions: randrange, randint, binomialvariate.

The possible values are a range, so the grid (step) is explicit. Fine
behaviour: steps of one grid point, recombination between the parents on the
grid, and repair that keeps the position on the grid (eg the same index into
a list that grew).
"""

import random as _random

from .base import Choice, Distribution, decide


class Integer(Distribution):
    __slots__ = ()

    @property
    def values(self):
        """The possible values, as a range."""
        raise NotImplementedError

    def _index(self, v):
        """Index of the grid point nearest to v, clipped to the range."""
        values = self.values
        i = round((v - values.start) / values.step)
        return min(max(i, 0), len(values) - 1)

    # -- fine behaviour ----------------------------------------------------------------

    def mutate(self, value, rng):
        values = self.values
        if len(values) < 2:
            return Choice(self, value)
        i = self._index(value)
        step = rng.choice((-1, 1))
        if not 0 <= i + step < len(values):
            step = -step
        return Choice(self, values[i + step])

    def crossover(self, value, other, rng):
        if not self.same_kind(other):
            return Distribution.crossover(self, value, other, rng)
        return self._between(value, other, other, rng)

    def convex_crossover(self, value, other1, other2, rng):
        if not self.same_kind(other1, other2):
            return Distribution.convex_crossover(self, value, other1, other2, rng)
        return self._between(value, other1, other2, rng)

    def _between(self, value, other1, other2, rng):
        idx = [self._index(v) for v in (value, other1.value, other2.value)]
        return Choice(self, self.values[rng.randint(min(idx), max(idx))])

    def distance(self, value, other):
        if not self.same_kind(other):
            return Distribution.distance(self, value, other)
        values = self.values
        span = abs(values[-1] - values[0]) if len(values) else 0
        if span == 0:
            return float(value != other.value)
        return min(1.0, abs(value - other.value) / span)

    def repair(self, prev, rng):
        values = self.values
        if type(prev.dist) is not type(self) or not len(values):
            return Distribution.repair(self, prev, rng)
        pv = prev.dist.values
        i = round((prev.value - pv.start) / pv.step)
        return Choice(self, values[min(max(i, 0), len(values) - 1)])


class IntRange(Integer):
    """randrange(start, stop, step) and randint(a, b): uniform over a range."""

    __slots__ = ()

    def sample(self, rng):
        r = self.params[0]
        return rng.randrange(r.start, r.stop, r.step)

    @property
    def values(self):
        return self.params[0]


class Binomial(Integer):
    """binomialvariate(n, p), on 0..n."""

    __slots__ = ()

    def sample(self, rng):
        return rng.binomialvariate(*self.params)

    @property
    def values(self):
        return range(self.params[0] + 1)


# -- rnd functions ------------------------------------------------------------------


def _int(x):
    """randrange accepts integral floats in Python 3.10 and 3.11."""
    if isinstance(x, float) and x.is_integer():
        return int(x)
    return x


def randrange(start, stop=None, step=1, *, name=None):
    if stop is None:
        return decide(IntRange(range(_int(start))), name)
    return decide(IntRange(range(_int(start), _int(stop), _int(step))), name)


def randint(a, b, *, name=None):
    return decide(IntRange(range(a, b + 1)), name)


def binomialvariate(n=1, p=0.5, *, name=None):
    return decide(Binomial(n, p), name)


RND = (randrange, randint) + ((binomialvariate,) if hasattr(_random, "binomialvariate") else ())
