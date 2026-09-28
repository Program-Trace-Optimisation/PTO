"""Sequence decisions: shuffle, sample, choices. Values are tuples.

Fine behaviour: swaps (and, when items can be replaced, replacements) that
keep a value valid: a permutation stays a permutation of the same items, a
sample has distinct items of the population, choices come from the population.
"""

from collections import Counter

from .base import Choice, Distribution, decide, frozen


class Permutation(Distribution):
    """shuffle(x): a permutation of x's items."""

    __slots__ = ()

    def sample(self, rng):
        items = list(self.params[0])
        rng.shuffle(items)
        return tuple(items)

    @property
    def items(self):
        return self.params[0]

    # -- fine behaviour: swaps --------------------------------------------------------

    def mutate(self, value, rng):
        if len(value) < 2:
            return Choice(self, value)
        return Choice(self, _swap(value, rng))

    def crossover(self, value, other, rng):
        if not self.same_kind(other):
            return Distribution.crossover(self, value, other, rng)
        return Choice(self, _toward(value, other.value, [], rng))

    def convex_crossover(self, value, other1, other2, rng):
        if not self.same_kind(other1, other2):
            return Distribution.convex_crossover(self, value, other1, other2, rng)
        v = _toward(value, other1.value, [], rng)
        return Choice(self, _toward(v, other2.value, [], rng))

    def distance(self, value, other):
        if not self.same_kind(other):
            return Distribution.distance(self, value, other)
        n = max(len(value), len(other.value))
        return _edit_distance(value, other.value, []) / max(1, n - 1)

    def repair(self, prev, rng):
        if type(prev.dist) is not type(self):
            return Distribution.repair(self, prev, rng)
        return Choice(self, _toward(self.sample(rng), prev.value, [], rng, full=True))


class Sample(Distribution):
    """sample(population, k): k items without replacement."""

    __slots__ = ()

    def sample(self, rng):
        population, k = self.params
        return tuple(rng.sample(population, k))

    @property
    def population(self):
        return self.params[0]

    @property
    def k(self):
        return self.params[1]

    def unused(self, value):
        """The items of the population not in value."""
        return _multiset_diff(self.population, value)

    # -- fine behaviour: swaps, or replacement by an unused item --------------------

    def mutate(self, value, rng):
        unused = self.unused(value)
        moves = (["swap"] if len(value) >= 2 else []) + (["replace"] if value and unused else [])
        if not moves:
            return Choice(self, value)
        if rng.choice(moves) == "swap":
            return Choice(self, _swap(value, rng))
        v = list(value)
        v[rng.randrange(len(v))] = rng.choice(unused)
        return Choice(self, tuple(v))

    def crossover(self, value, other, rng):
        if not self.same_kind(other):
            return Distribution.crossover(self, value, other, rng)
        return Choice(self, _toward(value, other.value, self.unused(value), rng))

    def convex_crossover(self, value, other1, other2, rng):
        if not self.same_kind(other1, other2):
            return Distribution.convex_crossover(self, value, other1, other2, rng)
        v = _toward(value, other1.value, self.unused(value), rng)
        return Choice(self, _toward(v, other2.value, self.unused(v), rng))

    def distance(self, value, other):
        if not self.same_kind(other):
            return Distribution.distance(self, value, other)
        n = max(len(value), len(other.value))
        return _edit_distance(value, other.value, self.unused(value)) / max(1, n)

    def repair(self, prev, rng):
        if type(prev.dist) is not type(self):
            return Distribution.repair(self, prev, rng)
        v = self.sample(rng)
        return Choice(self, _toward(v, prev.value, self.unused(v), rng, full=True))


class Choices(Distribution):
    """choices(population, weights, cum_weights=, k=): k items with replacement."""

    __slots__ = ()

    def sample(self, rng):
        population, weights, cum_weights, k = self.params
        return tuple(rng.choices(population, weights, cum_weights=cum_weights, k=k))

    def draw(self, rng):
        """One item, with the same weights."""
        population, weights, cum_weights, _ = self.params
        return rng.choices(population, weights, cum_weights=cum_weights)[0]

    @property
    def population(self):
        return self.params[0]

    @property
    def k(self):
        return self.params[3]

    # -- fine behaviour: position-wise --------------------------------------------

    def mutate(self, value, rng):
        if not value:
            return Choice(self, value)
        v = list(value)
        v[rng.randrange(len(v))] = self.draw(rng)
        return Choice(self, tuple(v))

    def crossover(self, value, other, rng):
        if not self.same_kind(other):
            return Distribution.crossover(self, value, other, rng)
        return self._mix(value, other, other, rng)

    def convex_crossover(self, value, other1, other2, rng):
        if not self.same_kind(other1, other2):
            return Distribution.convex_crossover(self, value, other1, other2, rng)
        return self._mix(value, other1, other2, rng)

    def _mix(self, value, other1, other2, rng):
        """Each position from one of the three parents, if valid here."""
        population = self.population
        v = list(value)
        for i in range(len(v)):
            x = rng.choice((value, other1.value, other2.value))
            if i < len(x) and x[i] in population:
                v[i] = x[i]
        return Choice(self, tuple(v))

    def distance(self, value, other):
        if not self.same_kind(other):
            return Distribution.distance(self, value, other)
        a, b = value, other.value
        diff = sum(x != y for x, y in zip(a, b)) + abs(len(a) - len(b))
        return diff / max(1, max(len(a), len(b)))

    def repair(self, prev, rng):
        if type(prev.dist) is not type(self):
            return Distribution.repair(self, prev, rng)
        population = self.population
        v = [x if x in population else self.draw(rng) for x in prev.value[: self.k]]
        v += [self.draw(rng) for _ in range(self.k - len(v))]
        return Choice(self, tuple(v))


# -- helpers --------------------------------------------------------------------------


def _swap(value, rng):
    v = list(value)
    i, j = rng.sample(range(len(v)), 2)
    v[i], v[j] = v[j], v[i]
    return tuple(v)


def _multiset_diff(a, b):
    return list((Counter(a) - Counter(b)).elements())


def _toward(seq1, seq2, unused, rng, full=False):
    """seq1 changed to agree with seq2 on a prefix (all of it if full), by
    swapping items of seq1 or replacing them with unused items."""
    out = list(seq1)
    n = min(len(seq1), len(seq2))
    if n == 0:
        return tuple(out)
    unused = list(unused)
    point = n if full else rng.randrange(n)
    for i in range(point):
        want = seq2[i]
        if out[i] == want:
            continue
        if want in out[i + 1 :]:  # swap it into place
            j = out.index(want, i + 1)
            out[i], out[j] = out[j], out[i]
        elif want in unused:  # replace
            unused.remove(want)
            unused.append(out[i])
            out[i] = want
    return tuple(out)


def _edit_distance(seq1, seq2, unused):
    """Swaps, replacements and insertions/deletions turning seq1 into seq2."""
    out = list(seq1)
    unused = list(unused)
    moves = abs(len(seq1) - len(seq2))
    for i in range(min(len(seq1), len(seq2))):
        want = seq2[i]
        if out[i] == want:
            continue
        moves += 1
        if want in out[i + 1 :]:
            j = out.index(want, i + 1)
            out[i], out[j] = out[j], out[i]
        elif want in unused:
            unused.remove(want)
            unused.append(out[i])
            out[i] = want
    return moves


# -- rnd functions ------------------------------------------------------------------


def shuffle(x, *, name=None):
    x[:] = decide(Permutation(tuple(x)), name)


def sample(population, k, *, counts=None, name=None):
    if counts is not None:
        population = [x for x, n in zip(population, counts) for _ in range(n)]
    return list(decide(Sample(frozen(population), k), name))


def choices(population, weights=None, *, cum_weights=None, k=1, name=None):
    dist = Choices(frozen(population), None if weights is None else tuple(weights),
                   None if cum_weights is None else tuple(cum_weights), k)
    return list(decide(dist, name))


RND = (shuffle, sample, choices)
