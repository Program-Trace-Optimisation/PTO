"""
Tests that each solver respects better=max and better=min.

Uses a 5-bit OneMax problem (fitness = sum of bits, optimal = 5 for max,
0 for min).  The problem is tiny, so every solver should reach near-optimal
in a modest number of evaluations; this makes the tests both fast and
reliable enough to use deterministic assertions.

If a solver hard-codes maximisation internally (ignoring the better
parameter), the min tests will fail because the solver will keep returning
high-fitness solutions instead of low-fitness ones.
"""

import random
import unittest

from pto.core.base import Op, Dist
from pto.core.base.tracer import tracer
from pto.solvers import (
    genetic_algorithm as GA,
    hill_climber as HC,
    random_search as RS,
    particle_swarm_optimisation as PSO,
)


# ============================================================
# Problem: 5-bit OneMax
# ============================================================

def onemax5():
    return [tracer.sample(i, Dist(random.choice, [0, 1])) for i in range(5)]


def fitness(sol):
    """fitness = number of 1s; range [0, 5]."""
    return sum(sol)


# ============================================================
# Helper
# ============================================================

def run_solver(SolverClass, better, seed=42, **solver_kwargs):
    random.seed(seed)
    op = Op(generator=onemax5, fitness=fitness)
    result = SolverClass(op, better=better, **solver_kwargs)()
    sol, fx = result[0], result[1]
    return sol.pheno, fx


# ============================================================
# Tests
# ============================================================

class TestOptimizationDirection(unittest.TestCase):
    """
    For each solver: better=max should converge toward all-ones (fx >= 4),
    better=min should converge toward all-zeros (fx <= 1).
    """

    # ------------------------------------------------------------------
    # Hill climber
    # ------------------------------------------------------------------

    def test_hill_climber_max(self):
        _, fx = run_solver(HC, max, n_generation=200)
        self.assertGreaterEqual(fx, 4, f"HC(better=max): fx={fx}, expected >= 4")

    def test_hill_climber_min(self):
        _, fx = run_solver(HC, min, n_generation=200)
        self.assertLessEqual(fx, 1, f"HC(better=min): fx={fx}, expected <= 1")

    # ------------------------------------------------------------------
    # Random search
    # ------------------------------------------------------------------

    def test_random_search_max(self):
        _, fx = run_solver(RS, max, n_generation=500)
        self.assertGreaterEqual(fx, 4, f"RS(better=max): fx={fx}, expected >= 4")

    def test_random_search_min(self):
        _, fx = run_solver(RS, min, n_generation=500)
        self.assertLessEqual(fx, 1, f"RS(better=min): fx={fx}, expected <= 1")

    # ------------------------------------------------------------------
    # Genetic algorithm
    # ------------------------------------------------------------------

    def test_genetic_algorithm_max(self):
        _, fx = run_solver(GA, max, n_generation=50, population_size=20)
        self.assertGreaterEqual(fx, 4, f"GA(better=max): fx={fx}, expected >= 4")

    def test_genetic_algorithm_min(self):
        _, fx = run_solver(GA, min, n_generation=50, population_size=20)
        self.assertLessEqual(fx, 1, f"GA(better=min): fx={fx}, expected <= 1")

    # ------------------------------------------------------------------
    # Particle swarm optimisation
    # ------------------------------------------------------------------

    def test_pso_max(self):
        _, fx = run_solver(PSO, max, n_iteration=100, n_particles=20)
        self.assertGreaterEqual(fx, 4, f"PSO(better=max): fx={fx}, expected >= 4")

    def test_pso_min(self):
        _, fx = run_solver(PSO, min, n_iteration=100, n_particles=20)
        self.assertLessEqual(fx, 1, f"PSO(better=min): fx={fx}, expected <= 1")


if __name__ == "__main__":
    unittest.main()
