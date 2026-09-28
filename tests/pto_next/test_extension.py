"""Extending pto_next: a new distribution module and a new search operator
module (the examples of the README), added as if they were files of the
distributions and search_operators packages."""

import unittest

from pto_next import SearchSpace, rnd, run
from pto_next import distributions, search_operators

from . import example_distribution, example_search_operator


def setUpModule():
    distributions._add(example_distribution)
    search_operators._add(example_search_operator)


def tearDownModule():
    del rnd.subset
    del search_operators.OPERATORS["mutate_two_points_ind"]


def generator():
    def team():
        return rnd.subset(["ann", "bob", "cy", "dee"])
    return [team() for i in range(3)]


def fitness(teams):
    return sum(len(t) for t in teams)


class TestNewDistribution(unittest.TestCase):

    def test_used_like_any_rnd_function(self):
        for naming in ("linear", "dynamic", "static"):
            for operators in ("fine", "coarse"):
                with self.subTest(naming=naming, operators=operators):
                    space = SearchSpace(generator, fitness, naming=naming, operators=operators, seed=0)
                    sol = space.create_ind()
                    self.assertEqual(len(sol.geno), 3)
                    self.assertEqual(space.play(sol.geno), sol)
                    child = space.crossover_ind(sol, space.mutate_ind(sol))
                    self.assertTrue(all(set(t) <= {"ann", "bob", "cy", "dee"} for t in child.pheno))

    def test_fine_mutation_changes_one_item(self):
        space = SearchSpace(generator, fitness, seed=1)
        for _ in range(20):
            sol = space.create_ind()
            [c] = [c for c in sol.geno.values()][:1]
            new = space.mutate_choice(c)
            self.assertEqual(len(set(c.value) ^ set(new.value)), 1)

    def test_outside_a_play(self):
        self.assertEqual(len(generator()), 3)

    def test_optimises(self):
        result = run(generator, fitness, better=max, seed=0, solver_args={"n_generation": 200})
        self.assertEqual(result.fitness, 12)


class TestNewSearchOperator(unittest.TestCase):

    def test_chosen_by_name(self):
        space = SearchSpace(generator, fitness, mutation="mutate_two_points_ind", seed=0)
        sol = space.create_ind()
        child = space.mutate_ind(sol)
        changed = sum(sol.geno[a] != child.geno[a] for a in sol.geno)
        self.assertLessEqual(changed, 2)

    def test_used_by_a_solver(self):
        result = run(generator, fitness, better=max, seed=0,
                     solver_args={"n_generation": 100, "mutation": "mutate_two_points_ind"})
        self.assertGreater(result.fitness, 6)


if __name__ == "__main__":
    unittest.main()
