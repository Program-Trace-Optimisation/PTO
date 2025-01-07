import math
import random
from collections import namedtuple

"""
Parameter formats by type:
- 'real': (min, max, range)  # range = max-min or 2*std_dev
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

rng_specs = {
    # Real-valued functions
    random.random: RNGSpec(type="real", params=lambda args, kwargs: (0, 1, 1)),
    random.uniform: RNGSpec(
        type="real",
        params=lambda args, kwargs: (
            args[0] if args else kwargs["a"],
            args[1] if len(args) > 1 else kwargs["b"],
            (args[1] if len(args) > 1 else kwargs["b"])
            - (args[0] if args else kwargs["a"]),
        ),
    ),
    random.triangular: RNGSpec(
        type="real",
        params=lambda args, kwargs: (
            args[0] if args else kwargs["low"],
            args[1] if len(args) > 1 else kwargs["high"],
            (args[1] if len(args) > 1 else kwargs["high"])
            - (args[0] if args else kwargs["low"]),
        ),
    ),
    random.betavariate: RNGSpec(type="real", params=lambda args, kwargs: (0, 1, 1)),
    random.gauss: RNGSpec(
        type="real",
        params=lambda args, kwargs: (
            -math.inf,
            math.inf,
            2 * (args[1] if len(args) > 1 else kwargs["sigma"]),
        ),
    ),
    random.normalvariate: RNGSpec(
        type="real",
        params=lambda args, kwargs: (
            -math.inf,
            math.inf,
            2 * (args[1] if len(args) > 1 else kwargs["sigma"]),
        ),
    ),
    random.expovariate: RNGSpec(
        type="real",
        params=lambda args, kwargs: (
            0,
            math.inf,
            2.0 / (args[0] if args else kwargs["lambd"]),
        ),
    ),
    random.gammavariate: RNGSpec(
        type="real",
        params=lambda args, kwargs: (
            0,
            math.inf,
            2
            * (
                (args[0] if args else kwargs["alpha"]) ** 0.5
                / (args[1] if len(args) > 1 else kwargs["beta"])
            ),
        ),
    ),
    random.lognormvariate: RNGSpec(
        type="real",
        params=lambda args, kwargs: (
            0,
            math.inf,
            2
            * (
                math.exp((args[1] if len(args) > 1 else kwargs["sigma"]) ** 2 - 1)
                * math.exp(
                    2 * (args[0] if args else kwargs["mu"])
                    + (args[1] if len(args) > 1 else kwargs["sigma"]) ** 2
                )
            )
            ** 0.5,
        ),
    ),
    random.vonmisesvariate: RNGSpec(
        type="real", params=lambda args, kwargs: (-math.pi, math.pi, 2 * math.pi)
    ),
    random.paretovariate: RNGSpec(
        type="real",
        params=lambda args, kwargs: (
            1,
            math.inf,
            2
            * (
                (args[0] if args else kwargs["alpha"])
                / (
                    (args[0] if args else kwargs["alpha"] - 1) ** 2
                    * (args[0] if args else kwargs["alpha"] - 2)
                )
            )
            ** 0.5,
        ),
    ),
    random.weibullvariate: RNGSpec(
        type="real",
        params=lambda args, kwargs: (
            0,
            math.inf,
            2
            * (
                1.0
                / (args[1] if len(args) > 1 else kwargs["beta"])
                * (
                    math.gamma(1 + 2.0 / (args[0] if args else kwargs["alpha"]))
                    - math.gamma(1 + 1.0 / (args[0] if args else kwargs["alpha"])) ** 2
                )
                ** 0.5
            ),
        ),
    ),
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
