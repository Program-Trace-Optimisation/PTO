"""
Test suite for compiled_names/run.py.

Tests that the compiled_names run() interface works end-to-end:
compile-time name injection -> fine_distributions -> base -> solver.
"""

import sys
import random
import importlib.util
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

def test_basic_optimization():
    """run() with hill_climber finds a good ONEMAX solution."""
    print("--- 1. Basic optimization (ONEMAX) ---")
    random.seed(42)
    (pheno, geno), fx, _ = run(
        onemax_generator, sum,
        gen_args=(10,),
        better=max,
        Solver=hill_climber,
        solver_args={"n_generation": 200},
    )
    assert isinstance(pheno, list), f"Expected list, got {type(pheno)}"
    assert len(pheno) == 10, f"Expected length 10, got {len(pheno)}"
    assert fx >= 5, f"Expected fitness >= 5 after 200 generations, got {fx}"
    print(f"Solution: {pheno}, fitness: {fx}")

    # Trace keys should have compiled structural names
    for key in geno:
        assert isinstance(key, str), f"Expected string key, got {type(key)}"
        assert "root/" in key, f"Expected 'root/' in key: {key}"
    print(f"Trace keys ({len(geno)}): all have compiled structural names [OK]")
    print()


def test_minimization():
    """run() works for minimization problems."""
    print("--- 2. Minimization (Sphere) ---")
    random.seed(42)
    (pheno, geno), fx, _ = run(
        sphere_generator, lambda x: sum(v ** 2 for v in x),
        gen_args=(3,),
        better=min,
        Solver=hill_climber,
        solver_args={"n_generation": 200},
    )
    assert isinstance(pheno, list), f"Expected list, got {type(pheno)}"
    assert len(pheno) == 3, f"Expected length 3, got {len(pheno)}"
    print(f"Solution: {[round(v, 4) for v in pheno]}, fitness: {round(fx, 4)}")
    print()


def test_nested_functions():
    """run() handles generators with nested function calls."""
    print("--- 3. Nested functions ---")
    random.seed(42)
    (pheno, geno), fx, _ = run(
        nested_func_generator, sum,
        better=max,
        Solver=hill_climber,
        solver_args={"n_generation": 100},
    )
    assert isinstance(pheno, list), f"Expected list, got {type(pheno)}"
    assert len(pheno) == 5, f"Expected length 5, got {len(pheno)}"
    # Check trace keys contain the nested function name
    has_pick = any("pick" in key for key in geno)
    assert has_pick, f"Expected 'pick' in trace keys: {list(geno.keys())}"
    print(f"Solution: {pheno}, fitness: {fx}")
    print(f"Trace keys reference nested function 'pick' [OK]")
    print()


def test_nested_loops():
    """run() handles generators with nested loops."""
    print("--- 4. Nested loops ---")
    random.seed(42)
    (pheno, geno), fx, _ = run(
        multi_loop_generator, lambda m: sum(sum(row) for row in m),
        better=max,
        Solver=hill_climber,
        solver_args={"n_generation": 100},
    )
    assert isinstance(pheno, list), f"Expected list, got {type(pheno)}"
    assert len(pheno) == 3, f"Expected 3 rows, got {len(pheno)}"
    assert all(len(row) == 4 for row in pheno), "Expected 4 columns per row"
    assert len(geno) == 12, f"Expected 12 trace entries, got {len(geno)}"
    print(f"Solution: {pheno}, fitness: {fx}")
    print(f"Trace entries: {len(geno)} [OK]")
    print()


def test_search_operators_mode():
    """run() with Solver='search_operators' returns an Op instance."""
    print("--- 5. Search operators mode ---")
    op = run(
        onemax_generator, sum,
        gen_args=(10,),
        better=max,
        Solver="search_operators",
    )
    # Op should support create_ind and evaluate_ind
    sol = op.create_ind()
    fx = op.evaluate_ind(sol)
    assert isinstance(sol.pheno, list), f"Expected list phenotype, got {type(sol.pheno)}"
    assert len(sol.pheno) == 10
    assert isinstance(fx, (int, float)), f"Expected numeric fitness, got {type(fx)}"

    # Trace keys should be compiled structural names
    for key in sol.geno:
        assert "root/" in key, f"Expected 'root/' in key: {key}"
    print(f"Op.create_ind() phenotype: {sol.pheno}")
    print(f"Op.evaluate_ind() fitness: {fx}")
    print(f"Structural trace keys [OK]")
    print()


def test_seed_reproducibility():
    """run() with seed= produces reproducible results."""
    print("--- 6. Seed reproducibility ---")
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
    assert pheno1 == pheno2, f"Seed reproducibility failed: {pheno1} != {pheno2}"
    assert fx1 == fx2, f"Fitness mismatch: {fx1} != {fx2}"
    print(f"Run 1: {pheno1}, fitness: {fx1}")
    print(f"Run 2: {pheno2}, fitness: {fx2}")
    print(f"Reproducible [OK]")
    print()


def test_mutation_preserves_structure():
    """Mutated individuals keep the same compiled trace keys."""
    print("--- 7. Mutation preserves trace structure ---")
    op = run(
        onemax_generator, sum,
        gen_args=(10,),
        better=max,
        Solver="search_operators",
    )
    sol = op.create_ind()
    mutant = op.mutate_position_wise_ind(sol)

    assert set(sol.geno.keys()) == set(mutant.geno.keys()), (
        f"Trace keys differ after mutation:\n"
        f"  original: {set(sol.geno.keys())}\n"
        f"  mutant:   {set(mutant.geno.keys())}"
    )
    print(f"Original: {sol.pheno}")
    print(f"Mutant:   {mutant.pheno}")
    print(f"Trace keys identical [OK]")
    print()


def test_crossover():
    """Crossover between two compiled individuals works."""
    print("--- 8. Crossover ---")
    op = run(
        onemax_generator, sum,
        gen_args=(10,),
        better=max,
        Solver="search_operators",
    )
    parent1 = op.create_ind()
    parent2 = op.create_ind()
    child = op.crossover_ind(parent1, parent2)

    assert isinstance(child.pheno, list), f"Expected list, got {type(child.pheno)}"
    assert len(child.pheno) == 10
    assert set(child.geno.keys()) == set(parent1.geno.keys()), (
        "Child trace keys differ from parents"
    )
    print(f"Parent 1: {parent1.pheno}")
    print(f"Parent 2: {parent2.pheno}")
    print(f"Child:    {child.pheno}")
    print(f"Crossover [OK]")
    print()


# ============================================================
# Run all tests
# ============================================================

if __name__ == "__main__":
    test_basic_optimization()
    test_minimization()
    test_nested_functions()
    test_nested_loops()
    test_search_operators_mode()
    test_seed_reproducibility()
    test_mutation_preserves_structure()
    test_crossover()

    print("=" * 50)
    print("All run tests passed.")
