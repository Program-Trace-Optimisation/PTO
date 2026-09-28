"""An example of a new distribution module, as it would be added to
pto_next/distributions/ (the README shows it): a random subset of items."""

from pto_next.distributions.base import Choice, Distribution, decide


class Subset(Distribution):
    """subset(items): each item is in or out with probability 1/2; the value
    is a tuple of the items in, in their order."""

    __slots__ = ()

    def sample(self, rng):
        return tuple(x for x in self.params[0] if rng.random() < 0.5)

    # fine behaviour: add or remove one item; take each item from either parent

    def mutate(self, value, rng):
        items = self.params[0]
        if not items:
            return Choice(self, value)
        x = rng.choice(items)
        keep = set(value) ^ {x}
        return Choice(self, tuple(i for i in items if i in keep))

    def crossover(self, value, other, rng):
        if not self.same_kind(other):
            return Distribution.crossover(self, value, other, rng)
        a, b = set(value), set(other.value)
        return Choice(self, tuple(x for x in self.params[0] if x in (a if rng.random() < 0.5 else b)))

    def distance(self, value, other):
        if not self.same_kind(other):
            return Distribution.distance(self, value, other)
        return len(set(value) ^ set(other.value)) / max(1, len(self.params[0]))


def subset(items, *, name=None):
    return decide(Subset(tuple(items)), name)


RND = (subset,)
