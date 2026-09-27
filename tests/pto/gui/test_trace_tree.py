"""Test trace_tree visualisation on five problem types.

Builds one solution per problem and checks that its trace tree can be
generated and saved (to a temporary directory).

Run as a script to regenerate the example figures in the current directory:
PDFs if the Graphviz binaries are on PATH, otherwise .dot source files that
can be rendered later with:
    dot -Tpdf trace_tree_onemax.dot -o trace_tree_onemax.pdf
The committed examples are in docs/images/trace_trees/.
"""

import os
import tempfile
import unittest

from pto import run

try:
    import graphviz  # noqa: F401
    import numpy  # noqa: F401  (used by some problems)
    from pto.gui.trace_tree import trace_tree, save_dot
except ImportError:
    trace_tree = None


def _make_op(generator, fitness, gen_args=(), fit_args=(), better=min):
    return run(
        generator, fitness,
        gen_args=gen_args, fit_args=fit_args,
        better=better, Solver="search_operators",
    )


def _largest(op, n=20):
    return max((op.create_ind() for _ in range(n)), key=lambda s: len(s.geno))


# ── Problems: each returns an individual ───────────────────────────
def onemax_ind():
    from pto.problems.onemax import generator, fitness
    return _make_op(generator, fitness, gen_args=(10,), better=max).create_ind()


def tsp_ind():  # Knuth shuffle
    from pto.problems.tsp import generator_knuth, fitness, make_problem_data
    N = 8
    dist = make_problem_data(N, random_state=0)
    return _make_op(generator_knuth, fitness, gen_args=(N,), fit_args=(dist,)).create_ind()


def gp_ind():  # symbolic regression
    from pto.problems.symbolic_regression import generator, fitness
    n_vars = 4
    func_set = [("and", 2), ("or", 2), ("not", 1)]
    term_set = [f"x[{i}]" for i in range(n_vars)]
    op = _make_op(
        generator, fitness,
        gen_args=(func_set, term_set, 4),
        fit_args=([[True] * n_vars], [True]),
    )
    return _largest(op)


def ge_ind():  # grammatical evolution
    from pto.problems.grammatical_evolution import generator, fitness, grammar, make_training_data
    n_vars = 3
    grammar = dict(grammar, **{"<varidx>": [[str(i)] for i in range(n_vars)]})
    X_train, y_train = make_training_data(20, n_vars)
    op = _make_op(generator, fitness, gen_args=(grammar,), fit_args=(X_train, y_train))
    return _largest(op)


def nn_ind():  # neural network
    from pto.problems.neural_network import generator, fitness, make_training_data
    n_inputs, max_hidden = 3, 4
    X_train, y_train = make_training_data(10, n_inputs)
    op = _make_op(
        generator, fitness,
        gen_args=(n_inputs, max_hidden, n_inputs),
        fit_args=(X_train, y_train),
    )
    return op.create_ind()


PROBLEMS = {"onemax": onemax_ind, "tsp": tsp_ind, "gp": gp_ind, "ge": ge_ind, "nn": nn_ind}


@unittest.skipIf(trace_tree is None, "graphviz or numpy not installed")
class TestTraceTree(unittest.TestCase):

    def test_trace_trees(self):
        with tempfile.TemporaryDirectory() as tmp:
            for name, make_ind in PROBLEMS.items():
                with self.subTest(problem=name):
                    ind = make_ind()
                    self.assertTrue(len(ind.geno) > 0)
                    dot = trace_tree(ind.geno, view=False)
                    self.assertIn("digraph", dot.source)
                    path = os.path.join(tmp, f"trace_tree_{name}")
                    save_dot(dot, path)
                    self.assertTrue(os.path.getsize(path + ".dot") > 0)


def _save(dot, name):
    """Try PDF render; fall back to saving .dot source."""
    fname = f"trace_tree_{name}"
    try:
        dot.render(fname, view=False, cleanup=True)
        print(f"  -> saved {fname}.pdf")
    except Exception:
        save_dot(dot, fname)
        print(f"  -> saved {fname}.dot  (render with: dot -Tpdf {fname}.dot -o {fname}.pdf)")


if __name__ == "__main__":
    for name, make_ind in PROBLEMS.items():
        ind = make_ind()
        print(f"{name:7} trace_size={len(ind.geno)}")
        _save(trace_tree(ind.geno, view=False), name)
