"""Tests for choosing between dynamic and static structured names: run(..., naming=...)."""

import random
import unittest

from pto import run, rnd
from pto import rnd as random_alias


def generator():
    return [rnd.choice([0, 1]) for i in range(5)]


def generator_alias():
    return [random_alias.choice([0, 1]) for i in range(5)]


def helper():
    return rnd.choice([0, 1])


def generator_outside_helper():
    return [helper() for i in range(5)]


class TestNaming(unittest.TestCase):

    def setUp(self):
        random.seed(0)

    def tearDown(self):
        run(generator, sum, Solver="search_operators")  # back to the default naming

    def test_both_namings_trace_every_call(self):
        for naming in ["dynamic", "static"]:
            for gen in [generator, generator_alias]:
                with self.subTest(naming=naming, generator=gen.__name__):
                    (pheno, geno), fx, _ = run(gen, sum, better=max, naming=naming,
                                               solver_args={"n_generation": 5})
                    self.assertEqual(len(geno), 5)
                    self.assertEqual(fx, sum(pheno))

    def test_static_names_come_from_the_source(self):
        op = run(generator, sum, Solver="search_operators", naming="static")
        key = next(iter(op.create_ind().geno))
        self.assertTrue(key.startswith("root/generator@"), key)

    def test_static_rejects_helper_outside_generator(self):
        with self.assertRaisesRegex(ValueError, "naming='dynamic'"):
            run(generator_outside_helper, sum, naming="static")
        (pheno, geno), fx, _ = run(generator_outside_helper, sum,
                                   solver_args={"n_generation": 1})
        self.assertEqual(len(geno), 5)

    def test_invalid_combinations(self):
        with self.assertRaises(ValueError):
            run(generator, sum, naming="static", name_type="lin")
        with self.assertRaises(ValueError):
            run(generator, sum, naming="bogus")

    def test_rnd_works_outside_run(self):
        run(generator, sum, Solver="search_operators", naming="static")
        self.assertIn(rnd.choice([7, 8]), [7, 8])


if __name__ == "__main__":
    unittest.main()
