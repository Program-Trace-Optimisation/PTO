"""Real-valued decisions: random, uniform, gauss, expovariate, ...

Fine behaviour: gaussian steps scaled to the distribution's spread, blending
between parents, and repair that keeps a value's relative position when the
parameters change.
"""

import math

from .base import Choice, Distribution, decide


class Real(Distribution):
    """A real-valued distribution.

    lo, hi: bounds of the support (may be infinite)
    scale:  typical spread (the support's width, or twice the std)
    loc:    anchor used when a value is carried over to changed parameters
    """

    __slots__ = ()
    circular = False

    @property
    def lo(self):
        return 0.0

    @property
    def hi(self):
        return math.inf

    @property
    def scale(self):
        return self.hi - self.lo

    @property
    def loc(self):
        return self.lo

    def clip(self, value):
        return min(max(self.lo, value), self.hi)

    # -- fine behaviour ----------------------------------------------------------------

    def mutate(self, value, rng):
        return Choice(self, self.clip(value + rng.gauss(0, 0.1 * self.scale)))

    def crossover(self, value, other, rng):
        if not self.same_kind(other):
            return Distribution.crossover(self, value, other, rng)
        if self.circular:  # blend along the shorter arc
            arc = (other.value - value + math.pi) % (2 * math.pi) - math.pi
            return Choice(self, self.clip(value + rng.random() * arc))
        return Choice(self, self.clip(rng.uniform(value, other.value)))

    def convex_crossover(self, value, other1, other2, rng):
        if self.circular or not self.same_kind(other1, other2):
            return Distribution.convex_crossover(self, value, other1, other2, rng)
        values = (value, other1.value, other2.value)
        return Choice(self, self.clip(rng.uniform(min(values), max(values))))

    def distance(self, value, other):
        if not self.same_kind(other):
            return Distribution.distance(self, value, other)
        delta = abs(value - other.value)
        if self.circular:
            return min(delta, 2 * math.pi - delta) / math.pi
        if self.scale == 0:
            return float(delta != 0)
        return min(1.0, delta / self.scale)

    def repair(self, prev, rng):
        p = prev.dist
        if not (type(p) is type(self) and 0 < p.scale < math.inf):
            return Distribution.repair(self, prev, rng)
        value = (prev.value - p.loc) / p.scale * self.scale + self.loc
        return Choice(self, self.clip(value))


class Uniform(Real):
    """uniform(a, b); random() is Uniform(0.0, 1.0)."""

    __slots__ = ()

    def sample(self, rng):
        a, b = self.params
        return a + (b - a) * rng.random()

    @property
    def lo(self):
        return min(self.params)

    @property
    def hi(self):
        return max(self.params)


class Triangular(Real):
    """triangular(low, high, mode)."""

    __slots__ = ()

    def sample(self, rng):
        return rng.triangular(*self.params)

    @property
    def lo(self):
        return min(self.params[:2])

    @property
    def hi(self):
        return max(self.params[:2])


class Beta(Real):
    """betavariate(alpha, beta), on [0, 1]."""

    __slots__ = ()

    def sample(self, rng):
        return rng.betavariate(*self.params)

    @property
    def hi(self):
        return 1.0


class Normal(Real):
    """gauss(mu, sigma) and normalvariate(mu, sigma): the same distribution."""

    __slots__ = ()

    def sample(self, rng):
        return rng.gauss(*self.params)

    @property
    def lo(self):
        return -math.inf

    @property
    def scale(self):
        return 2 * abs(self.params[1])

    @property
    def loc(self):
        return self.params[0]


class Exponential(Real):
    """expovariate(lambd): on [0, inf) for lambd > 0, (-inf, 0] for lambd < 0."""

    __slots__ = ()

    def sample(self, rng):
        return rng.expovariate(*self.params)

    @property
    def lo(self):
        return 0.0 if self.params[0] > 0 else -math.inf

    @property
    def hi(self):
        return math.inf if self.params[0] > 0 else 0.0

    @property
    def scale(self):
        return 2 / abs(self.params[0])

    @property
    def loc(self):
        return 0.0


class Gamma(Real):
    """gammavariate(alpha, beta), beta being a scale: std = sqrt(alpha) * beta."""

    __slots__ = ()

    def sample(self, rng):
        return rng.gammavariate(*self.params)

    @property
    def scale(self):
        alpha, beta = self.params
        return 2 * math.sqrt(alpha) * beta


class LogNormal(Real):
    """lognormvariate(mu, sigma)."""

    __slots__ = ()

    def sample(self, rng):
        return rng.lognormvariate(*self.params)

    @property
    def scale(self):
        mu, sigma = self.params
        return 2 * math.sqrt((math.exp(sigma**2) - 1) * math.exp(2 * mu + sigma**2))


class VonMises(Real):
    """vonmisesvariate(mu, kappa): an angle in [0, 2*pi), so circular."""

    __slots__ = ()
    circular = True

    def sample(self, rng):
        return rng.vonmisesvariate(*self.params)

    @property
    def hi(self):
        return 2 * math.pi

    def clip(self, value):
        return value % (2 * math.pi)


class Pareto(Real):
    """paretovariate(alpha), on [1, inf)."""

    __slots__ = ()

    def sample(self, rng):
        return rng.paretovariate(*self.params)

    @property
    def lo(self):
        return 1.0

    @property
    def scale(self):
        alpha = self.params[0]
        if alpha > 2:
            return 2 * math.sqrt(alpha / ((alpha - 1) ** 2 * (alpha - 2)))
        return 4 ** (1 / alpha) - (4 / 3) ** (1 / alpha)  # infinite variance: IQR


class Weibull(Real):
    """weibullvariate(alpha, beta): alpha is the scale, beta the shape."""

    __slots__ = ()

    def sample(self, rng):
        return rng.weibullvariate(*self.params)

    @property
    def scale(self):
        alpha, beta = self.params
        var = math.gamma(1 + 2 / beta) - math.gamma(1 + 1 / beta) ** 2
        return 2 * alpha * math.sqrt(var)


# -- rnd functions ------------------------------------------------------------------


def random(*, name=None):
    return decide(Uniform(0.0, 1.0), name)


def uniform(a, b, *, name=None):
    return decide(Uniform(a, b), name)


def triangular(low=0.0, high=1.0, mode=None, *, name=None):
    return decide(Triangular(low, high, mode), name)


def betavariate(alpha, beta, *, name=None):
    return decide(Beta(alpha, beta), name)


def gauss(mu=0.0, sigma=1.0, *, name=None):
    return decide(Normal(mu, sigma), name)


def normalvariate(mu=0.0, sigma=1.0, *, name=None):
    return decide(Normal(mu, sigma), name)


def expovariate(lambd=1.0, *, name=None):
    return decide(Exponential(lambd), name)


def gammavariate(alpha, beta, *, name=None):
    return decide(Gamma(alpha, beta), name)


def lognormvariate(mu, sigma, *, name=None):
    return decide(LogNormal(mu, sigma), name)


def vonmisesvariate(mu, kappa, *, name=None):
    return decide(VonMises(mu, kappa), name)


def paretovariate(alpha, *, name=None):
    return decide(Pareto(alpha), name)


def weibullvariate(alpha, beta, *, name=None):
    return decide(Weibull(alpha, beta), name)


RND = (random, uniform, triangular, betavariate, gauss, normalvariate, expovariate,
       gammavariate, lognormvariate, vonmisesvariate, paretovariate, weibullvariate)
