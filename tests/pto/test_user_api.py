"""
Tests that the user-facing API behaves as documented in README.md.

These mirror the README examples, so if one of them fails, either the code
or the README needs updating.
"""

import random
import sys
import unittest
from unittest import mock

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
        for solver in ["random_search", "hill_climber", "genetic_algorithm",
                       "particle_swarm_optimisation"]:
            with self.subTest(solver=solver):
                result = run(generator, sum, better=max, Solver=solver,
                             solver_args={"n_generation": 3})
                self.assertEqual(len(result), 3)
                (pheno, geno), fx, _ = result
                self.assertEqual(fx, sum(pheno))

    def test_pso_budget_names(self):
        for budget in ["n_generation", "n_iteration"]:
            with self.subTest(budget=budget):
                *_, history = run(generator, sum, better=max,
                                  Solver="particle_swarm_optimisation",
                                  solver_args={budget: 4, "return_history": True})
                self.assertEqual(len(history), 4 + 1)  # initial swarm + 4 iterations

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

    def test_callback_can_stop_search(self):
        calls = []
        def stop_after_3(state):
            calls.append(state)
            return len(calls) >= 3
        run(generator, sum, better=max, callback=stop_after_3,
            solver_args={"n_generation": 100})
        self.assertEqual(len(calls), 3)
        sol, fx, gen = calls[-1]
        self.assertEqual(fx, sum(sol.pheno))

    def test_seed_reproducible(self):
        results = [run(generator, sum, better=max, seed=42,
                       solver_args={"n_generation": 5})[0].pheno for _ in range(2)]
        self.assertEqual(results[0], results[1])

    def test_custom_solver_class(self):
        class one_shot:
            def __init__(self, op, better=max, callback=None):
                self.op = op
            def __call__(self):
                sol = self.op.create_ind()
                return sol, self.op.evaluate_ind(sol), 0
        (pheno, geno), fx, num_gen = run(generator, sum, Solver=one_shot)
        self.assertEqual(fx, sum(pheno))

    def test_search_operators(self):
        op = run(generator, sum, better=max, Solver="search_operators")
        sol = op.create_ind()
        self.assertEqual(op.evaluate_ind(sol), sum(sol.pheno))


def hamming(a, b):
    return sum(x != y for x, y in zip(a, b))


class TestOtherSolvers(unittest.TestCase):

    def setUp(self):
        random.seed(0)

    def test_population_solver_callback_state(self):
        states = []
        run(generator, sum, better=max, Solver="genetic_algorithm", callback=states.append,
            solver_args={"n_generation": 2, "population_size": 6})
        population, fitnesses, gen = states[-1]
        self.assertEqual(len(population), 6)
        self.assertEqual(fitnesses, [sum(s.pheno) for s in population])

    def test_novelty_search(self):
        (pheno, geno), fx, num_gen = run(
            generator, sum, better=max, Solver="novelty_search",
            solver_args={"behavior_distance": hamming, "n_generation": 3,
                         "population_size": 8})
        self.assertEqual(fx, sum(pheno))

    def test_novelty_search_uses_its_own_behavior_distance(self):
        from pto.solvers.novelty_search import novelty_search
        op = run(generator, sum, better=max, Solver="search_operators")
        novelty_search(op, behavior_distance=hamming, n_generation=1, population_size=4)()
        calls = []
        def counting(a, b):
            calls.append(1)
            return hamming(a, b)
        novelty_search(op, behavior_distance=counting, n_generation=1, population_size=4)()
        self.assertTrue(calls, "second run must use its own behavior_distance")


class TestLandscapeAnalysis(unittest.TestCase):

    def setUp(self):
        random.seed(0)

    def test_correlogram_walks(self):
        try:
            import numpy, matplotlib  # noqa: F401
        except ImportError:
            self.skipTest("numpy/matplotlib not installed")
        from pto.solvers import correlogram_walks
        op = run(generator, sum, better=max, Solver="search_operators")
        x_axis, y_axis = correlogram_walks(op, n_walks=5, walk_length=5, n_bins=5)()
        self.assertEqual(len(x_axis), len(y_axis))
        self.assertTrue(len(x_axis) > 0)

    def test_correlogram(self):
        try:
            import numpy, scipy, skgstat  # noqa: F401
        except ImportError:
            self.skipTest("numpy/scipy/scikit-gstat not installed")
        from pto.solvers import correlogram
        op = run(generator, sum, better=max, Solver="search_operators")
        result = correlogram(op, n_walks=5, walk_len=10)()
        self.assertTrue(len(result) > 0)


class TestSolverImport(unittest.TestCase):

    def test_unknown_solver(self):
        with self.assertRaisesRegex(ValueError, "Unknown solver 'no_such_solver'"):
            run(generator, sum, Solver="no_such_solver")

    def test_core_solvers_do_not_need_optional_dependencies(self):
        import pto.solvers
        self.assertNotIn("pto.solvers.correlogram", pto.solvers.__all__)
        with mock.patch.dict(sys.modules, {"skgstat": None}):
            sys.modules.pop("pto.solvers.correlogram", None)
            run(generator, sum, solver_args={"n_generation": 3})

    def test_lazy_solver_is_the_class_on_every_access(self):
        try:
            import numpy, matplotlib  # noqa: F401
        except ImportError:
            self.skipTest("numpy/matplotlib not installed")
        from pto.solvers.correlogram_walks import correlogram_walks as direct
        import pto.solvers
        for _ in range(2):
            from pto.solvers import correlogram_walks
            self.assertIs(correlogram_walks, direct)
            self.assertIs(pto.solvers.correlogram_walks, direct)

    def test_missing_dependency_is_reported(self):
        with mock.patch.dict(sys.modules, {"skgstat": None}):
            sys.modules.pop("pto.solvers.correlogram", None)
            # the solver's missing dependency is reported (skgstat, or numpy/scipy
            # first if those are missing too), not "Unknown solver"
            with self.assertRaises(ImportError) as cm:
                run(generator, sum, Solver="correlogram")
            self.assertIn(cm.exception.name, {"numpy", "scipy", "skgstat"})


if __name__ == "__main__":
    unittest.main()
