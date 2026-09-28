"""Regression tests for the fine distributions, their parameter specs and the trace operators."""

import copy
import random
import statistics
import unittest

from pto import run, rnd
from pto.core.base import Op, tracer
from pto.core.fine_distributions import Random_int, Random_real, Random_seq, rng_specs
from pto.core.fine_distributions.supp import shuffle


def spread(fun, *args, **kwargs):
    return rng_specs[fun].params(args, kwargs)[2]


class TestRealSpecs(unittest.TestCase):

    def test_spread_is_twice_the_std(self):
        random.seed(0)
        for fun, args in [(random.gammavariate, (2.0, 3.0)),
                          (random.weibullvariate, (2.0, 3.0)),
                          (random.weibullvariate, (5.0, 0.8)),
                          (random.lognormvariate, (0.5, 0.8)),
                          (random.expovariate, (0.5,)),
                          (random.gauss, (0, 2))]:
            with self.subTest(fun=fun.__name__, args=args):
                emp = 2 * statistics.pstdev(fun(*args) for _ in range(50000))
                self.assertAlmostEqual(spread(fun, *args), emp, delta=0.05 * emp)

    def test_pareto(self):
        self.assertAlmostEqual(spread(random.paretovariate, 3.0), 3**0.5)
        self.assertEqual(spread(random.paretovariate, 3.0),
                         spread(random.paretovariate, alpha=3.0))
        self.assertGreater(spread(random.paretovariate, 1.5), 0)  # infinite variance

    def test_default_arguments(self):
        self.assertEqual(spread(random.gauss), 2.0)
        self.assertEqual(spread(random.normalvariate), 2.0)
        self.assertEqual(spread(random.triangular), 1.0)
        self.assertEqual(spread(random.expovariate), 2.0)


class TestRandomReal(unittest.TestCase):

    def test_zero_width_distance(self):
        a = Random_real(random.uniform, 1, 1, val=1)
        self.assertEqual(a.distance(copy.copy(a)), 0.0)

    def test_gauss_repair_keeps_z_score(self):
        new = Random_real(random.gauss, 10, 2)
        new.repair(Random_real(random.gauss, 0, 1, val=0.7))
        self.assertAlmostEqual(new.val, 11.4)


class TestRandomInt(unittest.TestCase):

    def test_step_values_stay_on_grid(self):
        random.seed(0)
        a = Random_int(random.randrange, 0, 10, 2, val=2)
        b = Random_int(random.randrange, 0, 10, 2, val=8)
        values = set()
        for _ in range(200):
            values.add(a.crossover(b).val)
            values.add(a.convex_crossover(b, b).val)
            values.add(b.mutation().val)
        self.assertEqual(values, {2, 4, 6, 8})

    def test_size_counts_values(self):
        self.assertEqual(Random_int(random.randint, 0, 1, val=0).size(), 2)
        self.assertEqual(Random_int(random.randrange, 0, 10, 2, val=0).size(), 5)

    def test_single_value_distance(self):
        a = Random_int(random.randint, 3, 3, val=3)
        self.assertEqual(a.distance(copy.copy(a)), 0.0)


class TestRandomSeq(unittest.TestCase):

    def test_distance_is_a_number(self):
        a = Random_seq(shuffle, [0, 1, 2], val=[0, 1, 2])
        b = Random_seq(shuffle, [0, 1, 2], val=[1, 0, 2])
        self.assertEqual(a.distance(b), 1)

    def test_empty_sequence(self):
        random.seed(0)
        a = Random_seq(shuffle, [], val=[])
        for _ in range(20):
            self.assertEqual(a.mutation().val, [])
            self.assertEqual(a.crossover(copy.copy(a)).val, [])

    def test_distance_ind_on_permutations(self):
        def generator():
            x = list(range(6))
            rnd.shuffle(x)
            return x
        op = run(generator, sum, Solver="search_operators")
        self.assertIsInstance(op.distance_ind(op.create_ind(), op.create_ind()), int)


class TestOnePointCrossover(unittest.TestCase):

    def test_every_split_is_possible(self):
        random.seed(0)

        def generator():
            return [tracer.sample(i, Random_int(random.randint, 0, 1)) for i in range(4)]

        op = Op(generator=generator, fitness=sum, tracer=tracer)

        def constant(v):
            geno = {}
            for k, d in op.create_ind().geno.items():
                geno[k] = copy.copy(d)
                geno[k].val = v
            return op.fix_ind(geno)

        zeros, ones = constant(0), constant(1)
        from_first = {4 - sum(op.crossover_one_point_ind(zeros, ones).pheno)
                      for _ in range(300)}
        self.assertEqual(from_first, {0, 1, 2, 3, 4})


if __name__ == "__main__":
    unittest.main()
