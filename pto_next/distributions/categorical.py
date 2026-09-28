"""Categorical decisions: choice.

Fine behaviour: mutation picks a different option, and repair keeps the value
if it is still one of the options. Crossover and distance are coarse: options
have no order.
"""

from .base import Choice, Distribution, decide, frozen


class Categorical(Distribution):
    """choice(seq)."""

    __slots__ = ()

    def sample(self, rng):
        return rng.choice(self.params[0])

    @property
    def options(self):
        return self.params[0]

    # -- fine behaviour ----------------------------------------------------------------

    def mutate(self, value, rng):
        options = self.options
        for _ in range(20):  # rejection sampling, cheap for long option lists
            v = rng.choice(options)
            if v != value:
                return Choice(self, v)
        others = [o for o in options if o != value]
        return Choice(self, rng.choice(others) if others else value)

    def repair(self, prev, rng):
        if type(prev.dist) is not type(self):
            return Distribution.repair(self, prev, rng)
        options = self.options
        if prev.value in options:
            return Choice(self, prev.value)
        new = [o for o in options if o not in prev.dist.options]
        return Choice(self, rng.choice(new) if new else rng.choice(options))


# -- rnd functions ------------------------------------------------------------------


def choice(seq, *, name=None):
    return decide(Categorical(frozen(seq)), name)


RND = (choice,)
