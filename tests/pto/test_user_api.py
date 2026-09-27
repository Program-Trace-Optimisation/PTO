"""
Tests that the user-facing API behaves as documented in README.md.

These mirror the README examples, so if one of them fails, either the code
or the README needs updating.
"""

import random
import unittest

from pto import run, rnd


def generator():
    return [rnd.choice([0, 1]) for i in range(10)]


def generator_n(n):
    return [rnd.choice([0, 1]) for i in range(n)]


def fitness_offset(x, offset):
    return sum(x) + offset


class TestReadmeExamples(unittest.TestCase):

    def setUp(self):
        random.seed(0)

    def test_minimal_onemax(self):
        (pheno, geno), fx, num_gen = run(generator, sum, better=max)
        self.assertEqual(fx, sum(pheno))
        self.assertEqual(len(pheno), 10)
        self.assertIsInstance(geno, dict)
        self.assertIsInstance(num_gen, int)

    def test_extra_arguments(self):
        (pheno, geno), fx, num_gen = run(
            generator_n, fitness_offset, gen_args=(5,), fit_args=(100,), better=min
        )
        self.assertEqual(len(pheno), 5)
        self.assertEqual(fx, sum(pheno) + 100)

    def test_each_solver_returns_three_values(self):
        for solver, budget in [("random_search", "n_generation"),
                               ("hill_climber", "n_generation"),
                               ("genetic_algorithm", "n_generation"),
                               ("particle_swarm_optimisation", "n_iteration")]:
            with self.subTest(solver=solver):
                result = run(generator, sum, better=max, Solver=solver,
                             solver_args={budget: 3})
                self.assertEqual(len(result), 3)
                (pheno, geno), fx, _ = result
                self.assertEqual(fx, sum(pheno))

    def test_return_history(self):
        (pheno, geno), fx, history = run(
            generator, sum, better=max,
            solver_args={"n_generation": 25, "return_history": True},
        )
        self.assertIsInstance(history, list)
        self.assertTrue(len(history) > 0)

    def test_mutation_and_crossover_via_solver_args(self):
        for mutation in ["mutate_point_ind", "mutate_position_wise_ind",
                         "mutate_random_ind"]:
            with self.subTest(mutation=mutation):
                run(generator, sum, better=max,
                    solver_args={"mutation": mutation, "n_generation": 3})
        for crossover in ["crossover_uniform_ind", "crossover_one_point_ind"]:
            with self.subTest(crossover=crossover):
                run(generator, sum, better=max, Solver="genetic_algorithm",
                    solver_args={"crossover": crossover, "n_generation": 3})

    def test_callback(self):
        calls = []
        run(generator, sum, better=max, callback=calls.append,
            solver_args={"n_generation": 3})
        self.assertTrue(len(calls) > 0)

    def test_search_operators(self):
        op = run(generator, sum, better=max, Solver="search_operators")
        sol = op.create_ind()
        self.assertEqual(op.evaluate_ind(sol), sum(sol.pheno))


if __name__ == "__main__":
    unittest.main()
