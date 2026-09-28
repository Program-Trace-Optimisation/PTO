import math
import random
from collections import namedtuple

"""
Parameter formats by type:
- 'real': (min, max, range, loc)  # range = max-min or 2*std_dev;
                                  # repair keeps (val - loc) / range
- 'int':  (min, max, step)   # inclusive bounds
- 'cat':  sequence           # sequence
- 'seq':  (sequence, k)      # k is number of items to select/generate

This file covers all random number generators from Python's Random module (3.12):
- Real-valued: random, uniform, triangular, betavariate, normalvariate (gauss), 
              expovariate, gammavariate, lognormvariate, vonmisesvariate, 
              paretovariate, weibullvariate
- Integer-valued: randrange, randint, binomialvariate
- Categorical/Sequence: choice, choices, sample, shuffle
"""

RNGSpec = namedtuple("RNGSpec", ["type", "params"])

_REQUIRED = object()


def _arg(args, kwargs, i, name, default=_REQUIRED):
    """Argument i of a random call, given positionally, by name or by default."""
    if len(args) > i:
        return args[i]
    if name in kwargs:
        return kwargs[name]
    if default is _REQUIRED:
        raise TypeError(f"missing argument '{name}'")
    return default


def _gauss_params(args, kwargs):
    mu = _arg(args, kwargs, 0, "mu", 0.0)
    sigma = _arg(args, kwargs, 1, "sigma", 1.0)
    return (-math.inf, math.inf, 2 * sigma, mu)


def _lognorm_params(args, kwargs):
    mu = _arg(args, kwargs, 0, "mu")
    sigma = _arg(args, kwargs, 1, "sigma")
    std = ((math.exp(sigma**2) - 1) * math.exp(2 * mu + sigma**2)) ** 0.5
    return (0, math.inf, 2 * std, 0)


def _pareto_params(args, kwargs):
    alpha = _arg(args, kwargs, 0, "alpha")
    if alpha > 2:
        spread = 2 * (alpha / ((alpha - 1) ** 2 * (alpha - 2))) ** 0.5
    else:  # infinite variance: use the interquartile range
        spread = 4 ** (1 / alpha) - (4 / 3) ** (1 / alpha)
    return (1, math.inf, spread, 1)


def _weibull_params(args, kwargs):
    alpha = _arg(args, kwargs, 0, "alpha")  # scale
    beta = _arg(args, kwargs, 1, "beta")  # shape
    var = math.gamma(1 + 2 / beta) - math.gamma(1 + 1 / beta) ** 2
    return (0, math.inf, 2 * alpha * var**0.5, 0)


def _bounded(low_name, high_name, low_default=_REQUIRED, high_default=_REQUIRED):
    def params(args, kwargs):
        low = _arg(args, kwargs, 0, low_name, low_default)
        high = _arg(args, kwargs, 1, high_name, high_default)
        return (low, high, high - low, low)

    return params


rng_specs = {
    # Real-valued functions
    random.random: RNGSpec(type="real", params=lambda args, kwargs: (0, 1, 1, 0)),
    random.uniform: RNGSpec(type="real", params=_bounded("a", "b")),
    random.triangular: RNGSpec(type="real", params=_bounded("low", "high", 0.0, 1.0)),
    random.betavariate: RNGSpec(type="real", params=lambda args, kwargs: (0, 1, 1, 0)),
    random.gauss: RNGSpec(type="real", params=_gauss_params),
    random.normalvariate: RNGSpec(type="real", params=_gauss_params),
    random.expovariate: RNGSpec(
        type="real",
        params=lambda args, kwargs: (
            0,
            math.inf,
            2.0 / _arg(args, kwargs, 0, "lambd", 1.0),
            0,
        ),
    ),
    random.gammavariate: RNGSpec(
        type="real",
        params=lambda args, kwargs: (  # beta is a scale: std = sqrt(alpha) * beta
            0,
            math.inf,
            2 * _arg(args, kwargs, 0, "alpha") ** 0.5 * _arg(args, kwargs, 1, "beta"),
            0,
        ),
    ),
    random.lognormvariate: RNGSpec(type="real", params=_lognorm_params),
    random.vonmisesvariate: RNGSpec(
        type="real", params=lambda args, kwargs: (-math.pi, math.pi, 2 * math.pi, -math.pi)
    ),
    random.paretovariate: RNGSpec(type="real", params=_pareto_params),
    random.weibullvariate: RNGSpec(type="real", params=_weibull_params),
    # Integer-valued functions
    random.randrange: RNGSpec(
        type="int",
        params=lambda args, kwargs: (
            (0, args[0] - 1, 1)
            if len(args) == 1
            else (
                (args[0], args[1] - 1, args[2] if len(args) > 2 else 1)
                if args
                else (kwargs.get("start", 0), kwargs["stop"] - 1, kwargs.get("step", 1))
            )
        ),
    ),
    random.randint: RNGSpec(
        type="int",
        params=lambda args, kwargs: (
            args[0] if args else kwargs["a"],
            args[1] if len(args) > 1 else kwargs["b"],
            1,
        ),
    ),
    # Categorical/Sequence functions
    random.choice: RNGSpec(
        type="cat", params=lambda args, kwargs: args[0] if args else kwargs["seq"]
    ),
    random.choices: RNGSpec(
        type="seq",
        params=lambda args, kwargs: (
            args[0] if args else kwargs["population"],
            kwargs.get("k", 1) if "k" in kwargs else args[3] if len(args) > 3 else 1,
        ),
    ),
    random.sample: RNGSpec(
        type="seq",
        params=lambda args, kwargs: (
            args[0] if args else kwargs["population"],
            args[1] if len(args) > 1 else kwargs["k"],
        ),
    ),
}

# Handle binomialvariate (available only from v3.12)
if "binomialvariate" in dir(random):
    rng_specs[random.binomialvariate] = RNGSpec(
        type="int",
        params=lambda args, kwargs: (
            0,
            args[0] if args else kwargs.get("n", 1),  # upper bound is n
            1,
        ),
    )


# Add special case for shuffle
def shuffle(seq):
    """Wrapper for in-place shuffle returning a copy."""
    seq_copy = list(seq)
    random.shuffle(seq_copy)
    return seq_copy


rng_specs[shuffle] = RNGSpec(
    type="seq", params=lambda args, kwargs: (args[0], len(args[0]))
)
