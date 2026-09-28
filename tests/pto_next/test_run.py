"""pto_next.run: solvers, results, seeds, and the example problems."""

import random
import unittest
import warnings

from pto_next import Result, SearchSpace, rnd, run


def generator():
    return [rnd.choice([0, 1]) for i in range(10)]


def hamming(a, b):
    return sum(x != y for x, y in zip(a, b))


SOLVERS = {
    "random_search": {}, "hill_climber": {}, "genetic_algorithm": {"population_size": 6},
    "particle_swarm_optimisation": {"n_particles": 6},
    "novelty_search": {"behavior_distance": hamming, "population_size": 6},
}


class TestRun(unittest.TestCase):

    def test_readme_example(self):
        (pheno, geno), fx, num_gen = run(generator, sum, better=max)
        self.assertEqual(fx, sum(pheno))
        self.assertEqual(len(geno), 10)
        self.assertIsInstance(num_gen, int)

    def test_every_solver_and_naming(self):
        for solver, args in SOLVERS.items():
            for naming in ("linear", "dynamic", "static"):
                with self.subTest(solver=solver, naming=naming):
                    result = run(generator, sum, better=max, Solver=solver, naming=naming, seed=0,
                                 solver_args={"n_generation": 3, **args})
                    self.assertIsInstance(result, Result)
                    self.assertEqual(result.fitness, sum(result.best.pheno))
                    self.assertEqual(result.generations, 3)

    def test_history(self):
        result = run(generator, sum, solver_args={"n_generation": 5, "return_history": True})
        *_, history = result
        self.assertIs(history, result.history)
        self.assertEqual(len(history), 6)

    def test_seed_is_reproducible_and_restores_random(self):
        random.seed(123)
        before = random.getstate()
        a = run(generator, sum, Solver="genetic_algorithm", seed=4, solver_args={"n_generation": 5})
        b = run(generator, sum, Solver="genetic_algorithm", seed=4, solver_args={"n_generation": 5})
        self.assertEqual(a.best.pheno, b.best.pheno)
        self.assertEqual(random.getstate(), before)

    def test_search_operators(self):
        space = run(generator, sum, Solver="search_operators")
        self.assertIsInstance(space, SearchSpace)
        parent = space.create_ind()
        self.assertGreaterEqual(space.distance_ind(parent, space.mutate_ind(parent)), 0)

    def test_invalid_options(self):
        for kwargs in ({"naming": "str"}, {"operators": "fancy"}, {"Solver": "no_such_solver"}):
            with self.subTest(**kwargs), self.assertRaises(ValueError):
                run(generator, sum, **kwargs)


class TestExampleProblems(unittest.TestCase):
    """The problems of pto.problems (written for the old core's rnd) under this core."""

    def test_problems(self):
        warnings.filterwarnings("ignore")
        try:
            from pto.problems import as_classes as P
        except ImportError as e:
            self.skipTest(f"needs the examples extra: {e}")
        random.seed(0)
        problems = [P.OneMax(20), P.Sphere(10), P.HelloWorld(), P.TSP(N=10, random_state=0),
                    P.kTSP(N=10, k=4, random_state=0), P.Assignment(num_agents=4, num_tasks=6, random_state=0),
                    P.SymbolicRegression(10, 3), P.GrammaticalEvolution(10, 3), P.GraphEvolution(),
                    P.NeuralNetwork(2, 3, 1, 10)]
        for prob in problems:
            for naming in ("linear", "dynamic", "static"):
                with self.subTest(problem=type(prob).__name__, naming=naming):
                    space = SearchSpace(prob.generator, prob.fitness, prob.gen_args, prob.fit_args,
                                        naming=naming, seed=1)
                    for _ in range(5):
                        sol = space.mutate_position_wise_ind(space.create_ind())
                        self.assertEqual(repr(space.play(sol.geno).pheno), repr(sol.pheno))
                    run(prob.generator, prob.fitness, prob.gen_args, prob.fit_args, better=prob.better,
                        naming=naming, seed=1, solver_args={"n_generation": 3})


if __name__ == "__main__":
    unittest.main()
