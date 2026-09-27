"""
Smoke tests for the example problems in pto/problems.

Each problem is built through its class in as_classes.py (the interface used
by the experiment scripts) and run for a few hill-climber generations, to
catch problems that no longer construct or run.
"""

import random
import unittest

from pto import run

try:
    import numpy  # noqa: F401  (as_classes needs numpy)
    from pto.problems import as_classes as P
except ImportError:
    P = None


@unittest.skipIf(P is None, "numpy not installed")
class TestProblemsAsClasses(unittest.TestCase):

    def setUp(self):
        random.seed(0)

    def problems(self):
        return [
            P.OneMax(10),
            P.LeadingOnes(10),
            P.Sphere(5),
            P.HelloWorld(),
            P.TSP(N=5),
            P.kTSP(N=15, k=5),
            P.Assignment(num_agents=5, num_tasks=10),
            P.SymbolicRegression(30, 3),
            P.SymbolicRegression(60, 6),  # size used in the EvoStar 2025 experiments
            P.BFSCNF(6),
            P.GrammaticalEvolution(30, 4),
            P.GraphEvolution(),
            P.NeuralNetwork(n_inputs=2, max_hidden=3, n_outputs=1, n_samples=10),
        ]

    def test_problems_run(self):
        for prob in self.problems():
            with self.subTest(problem=prob.__class__.__name__):
                (pheno, geno), fx, _ = run(
                    prob.generator,
                    prob.fitness,
                    better=prob.better,
                    gen_args=prob.gen_args,
                    fit_args=prob.fit_args,
                    solver_args={"n_generation": 5},
                )
                self.assertEqual(fx, prob.fitness(pheno, *prob.fit_args))


class TestLambdaCalculus(unittest.TestCase):
    """pto.problems.LambdaCalculus is a package; its fitness must also work
    where signal.SIGALRM does not exist (Windows)."""

    def test_generator_and_fitness(self):
        from pto.problems.LambdaCalculus import lc_pto
        random.seed(0)
        (pheno, geno), fx, _ = run(
            lc_pto.tuple_generator,
            lambda e: lc_pto.unary_fitness(e, lc_pto.SUCC_TRAINING_CASES),
            better=min,
            solver_args={"n_generation": 5},
        )
        self.assertTrue(0 <= fx <= 1)
        # generic_fitness used signal.SIGALRM unconditionally
        g = lc_pto.generic_fitness(pheno, lc_pto.SUCC_TRAINING_CASES, lc_pto.apply_unary)
        self.assertTrue(0 <= g <= 1)


if __name__ == "__main__":
    unittest.main()
