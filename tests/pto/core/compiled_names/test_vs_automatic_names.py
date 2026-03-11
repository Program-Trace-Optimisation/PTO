"""
Tests that compiled_names and automatic_names produce equivalent behaviour.

Both are implementations of structured naming for PTO traces. Their trace
keys differ in format (compiled uses AST line.col; automatic uses bytecode
(line,idx)), but they must agree on:

  1. Trace length  — same number of rnd.X() calls traced per solution.
  2. Phenotype     — same solution values for the same random seed.
  3. Key structure — both keys start with 'root/'.
  4. Optimization  — both can improve fitness on the same problem.
  5. Operators     — mutation and crossover both preserve key count.
"""

import random
import sys
import importlib.util
import unittest

from pto.core.compiled_names.run import run as compiled_run
from pto.core.automatic_names.trans_run import run as auto_run
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
# Test generators — defined in a .py file (not a notebook)
# so that inspect.getsource() works reliably for both layers.
# ============================================================

def onemax_gen(size):
    return [rnd.choice([0, 1]) for i in range(size)]


def sphere_gen(n):
    return [rnd.uniform(-5.0, 5.0) for i in range(n)]


def nested_gen():
    def pick():
        return rnd.randint(0, 9)
    return [pick() for i in range(5)]


def matrix_gen():
    matrix = []
    for i in range(3):
        row = []
        for j in range(4):
            row.append(rnd.choice([0, 1]))
        matrix.append(row)
    return matrix


# ============================================================
# Helpers
# ============================================================

_SOLVERS = dict(Solver=hill_climber, solver_args={"n_generation": 100})


def _auto(gen, fitness, seed=None, **kwargs):
    return auto_run(gen, fitness, better=max, seed=seed, **_SOLVERS, **kwargs)


def _compiled(gen, fitness, seed=None, **kwargs):
    return compiled_run(gen, fitness, better=max, seed=seed, **_SOLVERS, **kwargs)


# ============================================================
# Tests
# ============================================================

class TestCompiledVsAutomaticNames(unittest.TestCase):

    # ----------------------------------------------------------
    # 1. Trace length
    # ----------------------------------------------------------

    def test_trace_length_onemax(self):
        """Both layers produce the same number of trace entries."""
        (_, geno_a), _, _ = _auto(onemax_gen, sum, gen_args=(10,))
        (_, geno_c), _, _ = _compiled(onemax_gen, sum, gen_args=(10,))
        self.assertEqual(len(geno_a), len(geno_c),
                         f"auto={len(geno_a)}, compiled={len(geno_c)}")

    def test_trace_length_sphere(self):
        (_, geno_a), _, _ = _auto(sphere_gen, lambda x: -sum(v**2 for v in x), gen_args=(5,))
        (_, geno_c), _, _ = _compiled(sphere_gen, lambda x: -sum(v**2 for v in x), gen_args=(5,))
        self.assertEqual(len(geno_a), len(geno_c))

    def test_trace_length_nested(self):
        (_, geno_a), _, _ = _auto(nested_gen, sum)
        (_, geno_c), _, _ = _compiled(nested_gen, sum)
        self.assertEqual(len(geno_a), len(geno_c))

    def test_trace_length_matrix(self):
        (_, geno_a), _, _ = _auto(matrix_gen, lambda m: sum(sum(r) for r in m))
        (_, geno_c), _, _ = _compiled(matrix_gen, lambda m: sum(sum(r) for r in m))
        self.assertEqual(len(geno_a), len(geno_c),
                         f"auto={len(geno_a)}, compiled={len(geno_c)}")

    # ----------------------------------------------------------
    # 2. Phenotype reproducibility with same seed
    # ----------------------------------------------------------

    def test_same_phenotype_onemax(self):
        """With the same seed both layers produce the same phenotype."""
        (pheno_a, _), _, _ = _auto(onemax_gen, sum, seed=42, gen_args=(10,))
        (pheno_c, _), _, _ = _compiled(onemax_gen, sum, seed=42, gen_args=(10,))
        self.assertEqual(pheno_a, pheno_c,
                         f"auto={pheno_a}\ncompiled={pheno_c}")

    def test_same_phenotype_sphere(self):
        (pheno_a, _), _, _ = _auto(sphere_gen, lambda x: -sum(v**2 for v in x),
                                   seed=7, gen_args=(4,))
        (pheno_c, _), _, _ = _compiled(sphere_gen, lambda x: -sum(v**2 for v in x),
                                       seed=7, gen_args=(4,))
        self.assertEqual(pheno_a, pheno_c)

    def test_same_phenotype_nested(self):
        (pheno_a, _), _, _ = _auto(nested_gen, sum, seed=99)
        (pheno_c, _), _, _ = _compiled(nested_gen, sum, seed=99)
        self.assertEqual(pheno_a, pheno_c)

    def test_same_phenotype_matrix(self):
        fitness = lambda m: sum(sum(r) for r in m)
        (pheno_a, _), _, _ = _auto(matrix_gen, fitness, seed=17)
        (pheno_c, _), _, _ = _compiled(matrix_gen, fitness, seed=17)
        self.assertEqual(pheno_a, pheno_c)

    # ----------------------------------------------------------
    # 3. Structural key format
    # ----------------------------------------------------------

    def test_auto_keys_start_with_root(self):
        (_, geno), _, _ = _auto(onemax_gen, sum, gen_args=(10,))
        for key in geno:
            self.assertIn("root/", key, f"Expected 'root/' in auto key: {key}")

    def test_compiled_keys_start_with_root(self):
        (_, geno), _, _ = _compiled(onemax_gen, sum, gen_args=(10,))
        for key in geno:
            self.assertIn("root/", key, f"Expected 'root/' in compiled key: {key}")

    def test_auto_keys_are_strings(self):
        (_, geno), _, _ = _auto(onemax_gen, sum, gen_args=(10,))
        for key in geno:
            self.assertIsInstance(key, str)

    def test_compiled_keys_are_strings(self):
        (_, geno), _, _ = _compiled(onemax_gen, sum, gen_args=(10,))
        for key in geno:
            self.assertIsInstance(key, str)

    # ----------------------------------------------------------
    # 4. Optimization — both can improve fitness
    # ----------------------------------------------------------

    def test_auto_optimizes_onemax(self):
        (pheno, _), fx, _ = _auto(onemax_gen, sum, gen_args=(10,))
        self.assertGreaterEqual(fx, 5, f"auto hill climber found only fx={fx}")

    def test_compiled_optimizes_onemax(self):
        (pheno, _), fx, _ = _compiled(onemax_gen, sum, gen_args=(10,))
        self.assertGreaterEqual(fx, 5, f"compiled hill climber found only fx={fx}")

    # ----------------------------------------------------------
    # 5. Operator consistency
    # ----------------------------------------------------------

    def test_auto_mutation_preserves_key_count(self):
        op = auto_run(onemax_gen, sum, gen_args=(10,), better=max,
                      Solver="search_operators")
        sol = op.create_ind()
        mutant = op.mutate_position_wise_ind(sol)
        self.assertEqual(len(sol.geno), len(mutant.geno))

    def test_compiled_mutation_preserves_key_count(self):
        op = compiled_run(onemax_gen, sum, gen_args=(10,), better=max,
                          Solver="search_operators")
        sol = op.create_ind()
        mutant = op.mutate_position_wise_ind(sol)
        self.assertEqual(len(sol.geno), len(mutant.geno))

    def test_auto_crossover_preserves_key_count(self):
        op = auto_run(onemax_gen, sum, gen_args=(10,), better=max,
                      Solver="search_operators")
        p1, p2 = op.create_ind(), op.create_ind()
        child = op.crossover_ind(p1, p2)
        self.assertEqual(len(child.geno), len(p1.geno))

    def test_compiled_crossover_preserves_key_count(self):
        op = compiled_run(onemax_gen, sum, gen_args=(10,), better=max,
                          Solver="search_operators")
        p1, p2 = op.create_ind(), op.create_ind()
        child = op.crossover_ind(p1, p2)
        self.assertEqual(len(child.geno), len(p1.geno))

    def test_auto_and_compiled_same_key_count_after_mutation(self):
        """After mutation, both layers should have the same number of keys.

        NOTE: auto and compiled layers share a class-level Op.tracer, so all
        operations for one layer must complete before switching to the other.
        """
        # auto layer: all operations before switching to compiled
        op_a = auto_run(onemax_gen, sum, gen_args=(10,), better=max,
                        Solver="search_operators")
        random.seed(5)
        sol_a = op_a.create_ind()
        mut_a = op_a.mutate_position_wise_ind(sol_a)

        # compiled layer: switching layers resets Op.tracer
        op_c = compiled_run(onemax_gen, sum, gen_args=(10,), better=max,
                            Solver="search_operators")
        random.seed(5)
        sol_c = op_c.create_ind()
        mut_c = op_c.mutate_position_wise_ind(sol_c)

        self.assertEqual(len(mut_a.geno), len(mut_c.geno))


if __name__ == "__main__":
    unittest.main()
