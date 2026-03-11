"""Test trace_tree visualisation on five problem types.

Generates one solution per problem and saves each tree.
If Graphviz binaries are on PATH, saves PDFs.
Otherwise, saves .dot source files that can be rendered later with:
    dot -Tpdf trace_tree_onemax.dot -o trace_tree_onemax.pdf

Usage::

    python test_trace_tree.py
"""

import random
import numpy as np
from pto import run, rnd
from pto.gui.trace_tree import trace_tree


def _make_op(generator, fitness, gen_args=(), fit_args=(), better=min):
    return run(
        generator, fitness,
        gen_args=gen_args, fit_args=fit_args,
        better=better, Solver="search_operators",
    )


def _save(dot, name):
    """Try PDF render; fall back to saving .dot source."""
    fname = f"trace_tree_{name}"
    try:
        dot.render(fname, view=False, cleanup=True)
        print(f"  -> saved {fname}.pdf")
    except Exception:
        path = f"{fname}.dot"
        with open(path, "w", encoding="utf-8") as f:
            f.write(dot.source)
        print(f"  -> saved {path}  (render with: dot -Tpdf {path} -o {fname}.pdf)")


# ── OneMax ──────────────────────────────────────────────────────────
def test_onemax():
    from pto.problems.onemax import generator, fitness
    op = _make_op(generator, fitness, gen_args=(10,), better=max)
    ind = op.create_ind()
    print(f"OneMax  pheno={ind.pheno}  trace_size={len(ind.geno)}")
    dot = trace_tree(ind.geno, view=False)
    _save(dot, "onemax")


# ── TSP (Knuth shuffle) ────────────────────────────────────────────
def test_tsp():
    from pto.problems.tsp import generator_knuth, fitness, make_problem_data
    N = 8
    dist = make_problem_data(N, random_state=0)
    op = _make_op(generator_knuth, fitness, gen_args=(N,), fit_args=(dist,))
    ind = op.create_ind()
    print(f"TSP     pheno={ind.pheno}  trace_size={len(ind.geno)}")
    dot = trace_tree(ind.geno, view=False)
    _save(dot, "tsp")


# ── Symbolic Regression (GP) ───────────────────────────────────────
def test_gp():
    from pto.problems.symbolic_regression import generator, fitness
    n_vars = 4
    func_set = [("and", 2), ("or", 2), ("not", 1)]
    term_set = [f"x[{i}]" for i in range(n_vars)]
    op = _make_op(
        generator, fitness,
        gen_args=(func_set, term_set, 4),
        fit_args=([[True] * n_vars], [True]),
    )
    best = max((op.create_ind() for _ in range(20)), key=lambda s: len(s.geno))
    print(f"GP      pheno={best.pheno}  trace_size={len(best.geno)}")
    dot = trace_tree(best.geno, view=False)
    _save(dot, "gp")


# ── Grammatical Evolution ──────────────────────────────────────────
def test_ge():
    from pto.problems.grammatical_evolution import generator, fitness, grammar, make_training_data
    n_vars = 3
    grammar["<varidx>"] = [[str(i)] for i in range(n_vars)]
    X_train, y_train = make_training_data(20, n_vars)
    op = _make_op(
        generator, fitness,
        gen_args=(grammar,),
        fit_args=(X_train, y_train),
    )
    best = max((op.create_ind() for _ in range(20)), key=lambda s: len(s.geno))
    print(f"GE      pheno={best.pheno}  trace_size={len(best.geno)}")
    dot = trace_tree(best.geno, view=False)
    _save(dot, "ge")


# ── Neural Network ─────────────────────────────────────────────────
def test_nn():
    from pto.problems.neural_network import generator, fitness, make_training_data
    n_inputs = 3
    max_hidden = 4
    n_outputs = n_inputs
    X_train, y_train = make_training_data(10, n_inputs)
    op = _make_op(
        generator, fitness,
        gen_args=(n_inputs, max_hidden, n_outputs),
        fit_args=(X_train, y_train),
    )
    ind = op.create_ind()
    print(f"NN      pheno=<network>  trace_size={len(ind.geno)}")
    dot = trace_tree(ind.geno, view=False)
    _save(dot, "nn")


if __name__ == "__main__":
    for name, fn in [
        ("OneMax", test_onemax),
        ("TSP", test_tsp),
        ("GP", test_gp),
        ("GE", test_ge),
        ("NN", test_nn),
    ]:
        try:
            fn()
        except Exception as e:
            print(f"  -> {name} FAILED: {e}")
    print("\nDone.")
