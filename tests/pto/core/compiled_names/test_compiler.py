"""
Tests for compiled_names/compiler.py.

Tests that compile_generator correctly injects name= into rnd.X() calls,
producing generators that work with PTO's existing rnd proxy and tracer.
"""

import random
import unittest

from pto.core.compiled_names.compiler import compile_generator
from pto.core.fine_distributions.traceables import rnd
from pto.core.base.tracer import tracer


# ============================================================
# Test generators — defined here so inspect.getsource works
# ============================================================

def onemax():
    return [rnd.choice([0, 1]) for i in range(10)]


def for_loop():
    result = []
    for i in range(5):
        result.append(rnd.randint(0, 100))
    return result


def nested_func():
    def pick_float():
        return rnd.uniform(-1.0, 1.0)
    return [pick_float() for i in range(4)]


def multi_call():
    pairs = []
    for i in range(3):
        x = rnd.random()
        y = rnd.random()
        pairs.append((x, y))
    return pairs


def nested_loops():
    matrix = []
    for i in range(3):
        row = []
        for j in range(4):
            row.append(rnd.randint(0, 9))
        matrix.append(row)
    return matrix


def nested_comp():
    return [[rnd.choice([0, 1]) for j in range(4)] for i in range(3)]


def conditional():
    result = []
    for i in range(6):
        coin = rnd.choice([0, 1])
        if coin:
            result.append(rnd.uniform(0, 1))
        else:
            result.append(rnd.randint(0, 100))
    return result


def multi_call_sites():
    def make_bit():
        return rnd.choice([0, 1])
    a = make_bit()
    b = make_bit()
    c = make_bit()
    return [a, b, c]


def func_with_args():
    def pick(lo, hi):
        return rnd.randint(lo, hi)
    return [pick(0, i + 1) for i in range(5)]


def while_loop():
    result = []
    i = 0
    while i < 5:
        result.append(rnd.random())
        i += 1
    return result


def mixed():
    blocks = []
    for i in range(3):
        block = [rnd.choice(["a", "b", "c"]) for j in range(4)]
        blocks.append(block)
    return blocks


def deep_nesting():
    def layer1():
        def layer2():
            return rnd.uniform(0, 1)
        return layer2()
    return [layer1() for i in range(3)]


def gauss_gen():
    return [rnd.gauss(0, 1) for i in range(5)]


def single_call():
    return rnd.choice(["red", "green", "blue"])


def no_rnd():
    return 42


# ============================================================
# Tests
# ============================================================

class TestCompiler(unittest.TestCase):

    def _assert_replay_works(self, gen_func):
        """Compile, run, verify replay reproduces the same solution."""
        compiled = compile_generator(gen_func)
        solution, trace = tracer.play(compiled, {})
        solution2, trace2 = tracer.play(compiled, trace)
        self.assertEqual(solution, solution2,
                         f"Replay mismatch: {solution} != {solution2}")
        self.assertEqual(set(trace.keys()), set(trace2.keys()),
                         "Trace keys differ after replay")
        return solution, trace

    def test_onemax_replay(self):
        _, trace = self._assert_replay_works(onemax)
        self.assertEqual(len(trace), 10)
        for key in trace:
            self.assertIn("comp", key)
            self.assertIn("choice", key)

    def test_for_loop_replay(self):
        _, trace = self._assert_replay_works(for_loop)
        self.assertEqual(len(trace), 5)
        for key in trace:
            self.assertIn("for", key)
            self.assertIn("randint", key)

    def test_nested_func_replay(self):
        self._assert_replay_works(nested_func)

    def test_multi_call_replay(self):
        _, trace = self._assert_replay_works(multi_call)
        self.assertEqual(len(trace), 6)

    def test_nested_loops_replay(self):
        _, trace = self._assert_replay_works(nested_loops)
        self.assertEqual(len(trace), 12)

    def test_nested_comp_replay(self):
        _, trace = self._assert_replay_works(nested_comp)
        self.assertEqual(len(trace), 12)

    def test_conditional_replay(self):
        # Conditional branches: trace length varies (6 coins + variable extras)
        self._assert_replay_works(conditional)

    def test_multi_call_sites_replay(self):
        _, trace = self._assert_replay_works(multi_call_sites)
        self.assertEqual(len(trace), 3)

    def test_func_with_args_replay(self):
        self._assert_replay_works(func_with_args)

    def test_while_loop_replay(self):
        _, trace = self._assert_replay_works(while_loop)
        self.assertEqual(len(trace), 5)
        for key in trace:
            self.assertIn("while", key)
            self.assertIn("random", key)

    def test_mixed_replay(self):
        _, trace = self._assert_replay_works(mixed)
        self.assertEqual(len(trace), 12)

    def test_deep_nesting_replay(self):
        self._assert_replay_works(deep_nesting)

    def test_gauss_gen_replay(self):
        self._assert_replay_works(gauss_gen)

    def test_single_call_replay(self):
        _, trace = self._assert_replay_works(single_call)
        self.assertEqual(len(trace), 1)

    def test_no_rnd_replay(self):
        _, trace = self._assert_replay_works(no_rnd)
        self.assertEqual(len(trace), 0)

    def test_compiled_source_attribute(self):
        compiled = compile_generator(onemax)
        self.assertTrue(hasattr(compiled, "_compiled_source"))
        self.assertTrue(hasattr(compiled, "_original_source"))

    def test_all_keys_have_root_prefix(self):
        """Compiled trace keys should start with 'root/'."""
        compiled = compile_generator(onemax)
        _, trace = tracer.play(compiled, {})
        for key in trace:
            self.assertIn("root/", key, f"Expected 'root/' in key: {key}")


if __name__ == "__main__":
    unittest.main()
