"""pto_next.distributions: sampling, parameters, and rnd."""

import math
import random
import statistics
import unittest

from pto_next import rnd
from pto_next.distributions.categorical import Categorical
from pto_next.distributions.integer import IntRange
from pto_next.distributions.real import Exponential, Gamma, LogNormal, Normal, Pareto, Triangular, Uniform, Weibull
from pto_next.trace import play

CALLS = [  # (function, args, kwargs)
    ("random", (), {}), ("uniform", (2, 5), {}), ("triangular", (), {}), ("triangular", (0, 10, 2), {}),
    ("betavariate", (2, 5), {}), ("gauss", (), {}), ("gauss", (1, 2), {}),
    ("expovariate", (0.5,), {}), ("gammavariate", (2, 3), {}),
    ("lognormvariate", (0.5, 0.8), {}), ("vonmisesvariate", (1, 2), {}), ("paretovariate", (3,), {}),
    ("weibullvariate", (2, 3), {}), ("randrange", (10,), {}), ("randrange", (0, 10, 2), {}),
    ("randint", (1, 6), {}), ("choice", ("abc",), {}), ("choices", ([1, 2, 3],), {"k": 4}),
    ("sample", (range(10), 3), {}),
]


def repair(prev, dist, rng):
    return dist.repair(prev, rng)


def played(function, *args, **kwargs):
    """The value of one rnd call made during a play, and its Choice."""
    value, trace = play(lambda: getattr(rnd, function)(*args, name="x", **kwargs), {},
                        random.Random(0), repair)
    return value, trace["x"]


class TestRnd(unittest.TestCase):

    def test_has_the_random_module_functions(self):
        for f in ["random", "uniform", "triangular", "betavariate", "gauss", "normalvariate",
                  "expovariate", "gammavariate", "lognormvariate", "vonmisesvariate", "paretovariate",
                  "weibullvariate", "randrange", "randint", "choice", "choices", "sample", "shuffle"]:
            self.assertTrue(callable(getattr(rnd, f)), f)

    def test_outside_a_play_same_as_random_module(self):
        for function, args, kwargs in CALLS:
            with self.subTest(function=function, args=args):
                random.seed(7)
                expected = getattr(random, function)(*args, **kwargs)
                random.seed(7)
                self.assertEqual(getattr(rnd, function)(*args, **kwargs), expected)
        # normalvariate is the same distribution as gauss, sampled with gauss's algorithm
        self.assertIsInstance(rnd.normalvariate(0, 1), float)

    def test_shuffle_outside_a_play(self):
        a, b = list(range(10)), list(range(10))
        random.seed(3)
        random.shuffle(a)
        random.seed(3)
        rnd.shuffle(b)
        self.assertEqual(a, b)


class TestDistributions(unittest.TestCase):

    def test_values_in_support(self):
        for function, args, kwargs in CALLS:
            with self.subTest(function=function, args=args):
                value, choice = played(function, *args, **kwargs)
                d = choice.dist
                if hasattr(d, "lo"):
                    self.assertTrue(d.lo <= value <= d.hi)
                elif hasattr(d, "values"):
                    self.assertIn(value, d.values)
                elif hasattr(d, "options"):
                    self.assertIn(value, d.options)

    def test_spread_is_twice_the_std(self):
        rng = random.Random(0)
        for d in [Normal(0, 2), Exponential(0.5), Gamma(2.0, 3.0), LogNormal(0.5, 0.8),
                  Weibull(2.0, 3.0), Weibull(5.0, 0.8)]:
            with self.subTest(dist=d):
                emp = 2 * statistics.pstdev(d.sample(rng) for _ in range(40000))
                self.assertAlmostEqual(d.scale, emp, delta=0.05 * emp)
        self.assertAlmostEqual(Pareto(3.0).scale, math.sqrt(3))
        self.assertGreater(Pareto(1.5).scale, 0)  # infinite variance

    def test_equal_calls_are_equal_distributions(self):
        self.assertEqual(played("randrange", 0, 9, 2)[1].dist, played("randrange", 0, 10, 2)[1].dist)
        self.assertEqual(played("randint", 1, 6)[1].dist, IntRange(range(1, 7)))
        self.assertEqual(played("gauss", 0, 1)[1].dist, played("normalvariate", 0, 1)[1].dist)
        self.assertEqual(played("choice", [1, 2])[1].dist, Categorical((1, 2)))
        self.assertNotEqual(Uniform(0, 1), Triangular(0, 1, None))

    def test_returned_sequences_are_copies(self):
        value, choice = played("sample", [1, 2, 3, 4], 2)
        value.append(99)
        self.assertEqual(len(choice.value), 2)
        self.assertIsInstance(choice.value, tuple)

    def test_shuffle_in_a_play(self):
        x = list(range(6))
        _, trace = play(lambda: rnd.shuffle(x, name="p"), {}, random.Random(1), repair)
        self.assertEqual(sorted(x), list(range(6)))
        self.assertEqual(tuple(x), trace["p"].value)

    def test_errors_like_random(self):
        with self.assertRaises(ValueError):
            played("randrange", 0)
        with self.assertRaises(IndexError):
            played("choice", [])


if __name__ == "__main__":
    unittest.main()
