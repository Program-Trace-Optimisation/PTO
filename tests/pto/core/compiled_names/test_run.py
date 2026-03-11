"""
Tests for compiled_names/run.py.

Tests that the compiled_names run() interface works end-to-end:
compile-time name injection -> fine_distributions -> base -> solver.
"""

import sys
import random
import importlib.util
import unittest

from pto.core.compiled_names.run import run
from pto.core.fine_distributions.traceables import rnd

# Load hill_climber without triggering solvers/__init__.py, which
# imports correlogram (requires optional skgstat dependency).
_spec = importlib.util.spec_from_file_location(
    "pto.solvers.hill_climber",
    sys.modules["pto"].__path__[0] + "/solvers/hill_climber.py",
)
_hc_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_hc_module)
hill_climber = _hc_module.hill_climber


# ============================================================
# Test generators — defined here so inspect.getsource works
# ============================================================

def onemax_generator(size):
    return [rnd.choice([0, 1]) for i in range(size)]


def sphere_generator(n):
    return [rnd.uniform(-5.0, 5.0) for i in range(n)]


def nested_func_generator():
    def pick():
        return rnd.randint(0, 10)
    return [pick() for i in range(5)]


def multi_loop_generator():
    matrix = []
    for i in range(3):
        row = []
        for j in range(4):
            row.append(rnd.choice([0, 1]))
        matrix.append(row)
    return matrix


# ============================================================
# Tests
# ============================================================

class TestCompiledNamesRun(unittest.TestCase):

    def test_basic_optimization(self):
        """run() with hill_climber finds a good ONEMAX solution."""
        random.seed(42)
        (pheno, geno), fx, _ = run(
            onemax_generator, sum,
            gen_args=(10,),
            better=max,
            Solver=hill_climber,
            solver_args={"n_generation": 200},
        )
        self.assertIsInstance(pheno, list)
        self.assertEqual(len(pheno), 10)
        self.assertGreaterEqual(fx, 5, f"Expected fitness >= 5 after 200 generations, got {fx}")
        for key in geno:
            self.assertIsInstance(key, str)
            self.assertIn("root/", key)

    def test_minimization(self):
        """run() works for minimization problems."""
        random.seed(42)
        (pheno, geno), fx, _ = run(
            sphere_generator, lambda x: sum(v ** 2 for v in x),
            gen_args=(3,),
            better=min,
            Solver=hill_climber,
            solver_args={"n_generation": 200},
        )
        self.assertIsInstance(pheno, list)
        self.assertEqual(len(pheno), 3)

    def test_nested_functions(self):
        """run() handles generators with nested function calls."""
        random.seed(42)
        (pheno, geno), fx, _ = run(
            nested_func_generator, sum,
            better=max,
            Solver=hill_climber,
            solver_args={"n_generation": 100},
        )
        self.assertIsInstance(pheno, list)
        self.assertEqual(len(pheno), 5)
        has_pick = any("pick" in key for key in geno)
        self.assertTrue(has_pick, f"Expected 'pick' in trace keys: {list(geno.keys())}")

    def test_nested_loops(self):
        """run() handles generators with nested loops."""
        random.seed(42)
        (pheno, geno), fx, _ = run(
            multi_loop_generator, lambda m: sum(sum(row) for row in m),
            better=max,
            Solver=hill_climber,
            solver_args={"n_generation": 100},
        )
        self.assertIsInstance(pheno, list)
        self.assertEqual(len(pheno), 3)
        self.assertTrue(all(len(row) == 4 for row in pheno))
        self.assertEqual(len(geno), 12)

    def test_search_operators_mode(self):
        """run() with Solver='search_operators' returns an Op instance."""
        op = run(
            onemax_generator, sum,
            gen_args=(10,),
            better=max,
            Solver="search_operators",
        )
        sol = op.create_ind()
        fx = op.evaluate_ind(sol)
        self.assertIsInstance(sol.pheno, list)
        self.assertEqual(len(sol.pheno), 10)
        self.assertIsInstance(fx, (int, float))
        for key in sol.geno:
            self.assertIn("root/", key)

    def test_seed_reproducibility(self):
        """run() with seed= produces reproducible results."""
        (pheno1, _), fx1, _ = run(
            onemax_generator, sum,
            gen_args=(10,),
            better=max,
            Solver=hill_climber,
            solver_args={"n_generation": 50},
            seed=123,
        )
        (pheno2, _), fx2, _ = run(
            onemax_generator, sum,
            gen_args=(10,),
            better=max,
            Solver=hill_climber,
            solver_args={"n_generation": 50},
            seed=123,
        )
        self.assertEqual(pheno1, pheno2)
        self.assertEqual(fx1, fx2)

    def test_mutation_preserves_trace_keys(self):
        """Mutated individuals keep the same compiled trace keys."""
        op = run(
            onemax_generator, sum,
            gen_args=(10,),
            better=max,
            Solver="search_operators",
        )
        sol = op.create_ind()
        mutant = op.mutate_position_wise_ind(sol)
        self.assertEqual(
            set(sol.geno.keys()), set(mutant.geno.keys()),
            "Trace keys differ after mutation"
        )

    def test_crossover(self):
        """Crossover between two compiled individuals works."""
        op = run(
            onemax_generator, sum,
            gen_args=(10,),
            better=max,
            Solver="search_operators",
        )
        parent1 = op.create_ind()
        parent2 = op.create_ind()
        child = op.crossover_ind(parent1, parent2)
        self.assertIsInstance(child.pheno, list)
        self.assertEqual(len(child.pheno), 10)
        self.assertEqual(
            set(child.geno.keys()), set(parent1.geno.keys()),
            "Child trace keys differ from parents"
        )


if __name__ == "__main__":
    unittest.main()
