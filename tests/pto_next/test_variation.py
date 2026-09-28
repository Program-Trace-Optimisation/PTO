"""How the decisions of each distribution vary, fine (the distribution's own
methods) and coarse (those of Distribution): results are always valid."""

import math
import random
import unittest
from collections import Counter

from pto_next import Choice, Distribution
from pto_next.distributions.categorical import Categorical
from pto_next.distributions.integer import IntRange
from pto_next.distributions.real import (Beta, Exponential, Gamma, LogNormal, Normal, Pareto,
                                         Triangular, Uniform, VonMises, Weibull)
from pto_next.distributions.sequences import Choices, Permutation, Sample

DISTS = [
    Uniform(-1, 1), Uniform(2, 2), Triangular(0, 10, 2), Beta(2, 5), Normal(0, 2), Exponential(0.5),
    Exponential(-2), Gamma(2, 3), LogNormal(0, 0.5), VonMises(1, 2), Pareto(3), Weibull(2, 3),
    IntRange(range(0, 10, 2)), IntRange(range(10, 0, -3)), IntRange(range(5, 6)),
    Categorical("abcd"), Categorical((1,)), Permutation(tuple(range(6))), Permutation((1, 1, 2)),
    Sample(range(8), 3), Sample("aab", 2), Choices("xyz", None, None, 4), Choices((1, 2), (9, 1), None, 3),
]


def valid(c):
    d, v = c.dist, c.value
    if hasattr(d, "lo"):
        return d.lo <= v <= d.hi
    if hasattr(d, "values"):
        return v in d.values
    if hasattr(d, "options"):
        return v in d.options
    if isinstance(d, Permutation):
        return Counter(v) == Counter(d.items)
    if isinstance(d, Sample):
        return len(v) == d.k and not Counter(v) - Counter(d.population)
    if isinstance(d, Choices):
        return len(v) == d.k and all(x in d.population for x in v)
    raise AssertionError(d)


def variation(d, fine):
    """The class whose methods vary d's decisions (as SearchSpace does)."""
    return type(d) if fine else Distribution


class TestVariation(unittest.TestCase):

    def setUp(self):
        self.rng = random.Random(0)

    def choice(self, d):
        return Choice(d, d.sample(self.rng))

    def test_results_are_valid(self):
        for fine in (False, True):
            for d in DISTS:
                with self.subTest(fine=fine, dist=d):
                    V = variation(d, fine)
                    for _ in range(50):
                        a, b, c = self.choice(d), self.choice(d), self.choice(d)
                        for out in (V.mutate(d, a.value, self.rng), V.crossover(d, a.value, b, self.rng),
                                    V.convex_crossover(d, a.value, b, c, self.rng)):
                            self.assertEqual(out.dist, d)
                            self.assertTrue(valid(out), out)
                        self.assertTrue(0 <= V.distance(d, a.value, b) <= 1)
                        self.assertEqual(V.distance(d, a.value, a), 0)

    def test_repair_to_changed_parameters_is_valid(self):
        pairs = [(Uniform(0, 1), Uniform(5, 10)), (Normal(0, 1), Normal(10, 2)),
                 (IntRange(range(10)), IntRange(range(4))), (Categorical("abc"), Categorical("cde")),
                 (Permutation((1, 2, 3)), Permutation((1, 2, 3, 4))), (Sample(range(5), 2), Sample(range(3), 3)),
                 (Choices("ab", None, None, 2), Choices("bc", None, None, 3)), (Uniform(0, 1), IntRange(range(3)))]
        for fine in (False, True):
            for old, new in pairs:
                with self.subTest(fine=fine, old=old, new=new):
                    for _ in range(30):
                        out = variation(new, fine).repair(new, self.choice(old), self.rng)
                        self.assertEqual(out.dist, new)
                        self.assertTrue(valid(out), out)

    def test_fine_repair_carries_the_value_over(self):
        rng = self.rng
        self.assertAlmostEqual(Normal(10, 2).repair(Choice(Normal(0, 1), 0.7), rng).value, 11.4)
        self.assertAlmostEqual(Uniform(0, 8).repair(Choice(Uniform(0, 1), 0.25), rng).value, 2)
        self.assertEqual(IntRange(range(20)).repair(Choice(IntRange(range(10)), 3), rng).value, 3)
        self.assertEqual(Categorical("xb").repair(Choice(Categorical("abc"), "b"), rng).value, "b")

    def test_fine_int_mutation_moves_one_step(self):
        d = IntRange(range(0, 10, 2))
        self.assertEqual({d.mutate(4, self.rng).value for _ in range(50)}, {2, 6})
        self.assertEqual({d.mutate(8, self.rng).value for _ in range(50)}, {6})

    def test_circular_values_wrap(self):
        d = VonMises(0, 1)
        self.assertAlmostEqual(d.distance(0.1, Choice(d, 2 * math.pi - 0.1)), 0.2 / math.pi)
        for _ in range(50):
            v = d.crossover(0.1, Choice(d, 2 * math.pi - 0.1), self.rng).value
            self.assertTrue(v <= 0.1 or v >= 2 * math.pi - 0.1, v)  # the short way round

    def test_other_kind_of_parent_falls_back_to_coarse(self):
        u, n = Uniform(0, 1), Normal(0, 1)
        outs = [u.crossover(0.5, Choice(n, 3.0), self.rng) for _ in range(40)]
        self.assertIn(Choice(u, 0.5), outs)  # one parent or the other, nothing else
        self.assertIn(Choice(n, 3.0), outs)
        self.assertTrue(all(o in (Choice(u, 0.5), Choice(n, 3.0)) for o in outs))
        self.assertEqual(u.distance(0.5, Choice(n, 0.5)), 1.0)


if __name__ == "__main__":
    unittest.main()
