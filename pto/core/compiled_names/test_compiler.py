"""
Test suite for the name-compiling generator transformer.

Tests that the compiler correctly injects name= into rnd.X() calls,
producing generators that work with PTO's existing rnd proxy and tracer.
"""

import random
from pto.core.compiled_names.compiler import compile_generator
from pto.core.fine_distributions.traceables import rnd
from pto.core.base.tracer import tracer


def run_test(name, gen_func, check_trace=None):
    """
    Compile a generator, run it via the tracer, verify replay works.
    """
    print(f"--- {name} ---")

    compiled = compile_generator(gen_func)
    print(f"Compiled source:\n{compiled._compiled_source}\n")

    # Play: run with empty trace to generate fresh solution
    solution, trace = tracer.play(compiled, {})
    print(f"Solution: {solution}")
    print(f"Trace ({len(trace)} entries):")
    for k, v in trace.items():
        print(f"  {k} = {v.val}")

    # Replay: run with the trace to reproduce the solution
    solution2, trace2 = tracer.play(compiled, trace)
    assert solution == solution2, f"Replay mismatch: {solution} != {solution2}"
    print(f"Replay:  {solution2}  [OK]")

    assert set(trace.keys()) == set(trace2.keys()), "Trace keys differ after replay"

    if check_trace:
        check_trace(trace)

    print()


# ============================================================
# Test generators — use rnd (PTO's traceable random proxy)
# ============================================================

# 1. List comprehension with rnd.choice
def onemax():
    return [rnd.choice([0, 1]) for i in range(10)]


# 2. For loop with rnd.randint
def for_loop():
    result = []
    for i in range(5):
        result.append(rnd.randint(0, 100))
    return result


# 3. Nested function
def nested_func():
    def pick_float():
        return rnd.uniform(-1.0, 1.0)
    return [pick_float() for i in range(4)]


# 4. Multiple rnd calls per iteration
def multi_call():
    pairs = []
    for i in range(3):
        x = rnd.random()
        y = rnd.random()
        pairs.append((x, y))
    return pairs


# 5. Nested loops
def nested_loops():
    matrix = []
    for i in range(3):
        row = []
        for j in range(4):
            row.append(rnd.randint(0, 9))
        matrix.append(row)
    return matrix


# 6. Nested comprehensions
def nested_comp():
    return [[rnd.choice([0, 1]) for j in range(4)] for i in range(3)]


# 7. Conditional logic
def conditional():
    result = []
    for i in range(6):
        coin = rnd.choice([0, 1])
        if coin:
            result.append(rnd.uniform(0, 1))
        else:
            result.append(rnd.randint(0, 100))
    return result


# 8. Multiple call sites for same nested function
def multi_call_sites():
    def make_bit():
        return rnd.choice([0, 1])
    a = make_bit()
    b = make_bit()
    c = make_bit()
    return [a, b, c]


# 9. Nested function with arguments
def func_with_args():
    def pick(lo, hi):
        return rnd.randint(lo, hi)
    return [pick(0, i + 1) for i in range(5)]


# 10. While loop
def while_loop():
    result = []
    i = 0
    while i < 5:
        result.append(rnd.random())
        i += 1
    return result


# 11. Mixed for + comprehension
def mixed():
    blocks = []
    for i in range(3):
        block = [rnd.choice(["a", "b", "c"]) for j in range(4)]
        blocks.append(block)
    return blocks


# 12. Deeply nested functions
def deep_nesting():
    def layer1():
        def layer2():
            return rnd.uniform(0, 1)
        return layer2()
    return [layer1() for i in range(3)]


# 13. rnd.gauss
def gauss_gen():
    return [rnd.gauss(0, 1) for i in range(5)]


# 14. Single rnd call (no loop)
def single_call():
    return rnd.choice(["red", "green", "blue"])


# 15. No rnd calls
def no_rnd():
    return 42


# ============================================================
# Assertion helpers
# ============================================================

def check_len(trace, expected):
    assert len(trace) == expected, f"Expected {expected} trace entries, got {len(trace)}"


def assert_key_pattern(trace, loop_type, rnd_method, expected_count):
    assert len(trace) == expected_count, (
        f"Expected {expected_count} trace entries, got {len(trace)}"
    )
    for key in trace:
        assert loop_type in key, f"Expected '{loop_type}' in key: {key}"
        assert rnd_method in key, f"Expected '{rnd_method}' in key: {key}"


# ============================================================
# Run all tests
# ============================================================

if __name__ == "__main__":
    random.seed(42)

    run_test("1. ONEMAX (list comprehension)", onemax,
             lambda t: assert_key_pattern(t, "comp", "choice", 10))

    run_test("2. For loop", for_loop,
             lambda t: assert_key_pattern(t, "for", "randint", 5))

    run_test("3. Nested function", nested_func)

    run_test("4. Multiple rnd calls per iteration", multi_call,
             lambda t: check_len(t, 6))

    run_test("5. Nested loops", nested_loops,
             lambda t: check_len(t, 12))

    run_test("6. Nested comprehensions", nested_comp,
             lambda t: check_len(t, 12))

    run_test("7. Conditional branches", conditional)

    run_test("8. Multiple call sites", multi_call_sites,
             lambda t: check_len(t, 3))

    run_test("9. Nested function with args", func_with_args)

    run_test("10. While loop", while_loop,
             lambda t: assert_key_pattern(t, "while", "random", 5))

    run_test("11. Mixed for + comprehension", mixed,
             lambda t: check_len(t, 12))

    run_test("12. Deeply nested functions", deep_nesting)

    run_test("13. rnd.gauss", gauss_gen)

    run_test("14. Single rnd call (no loop)", single_call,
             lambda t: check_len(t, 1))

    run_test("15. No rnd calls", no_rnd,
             lambda t: check_len(t, 0))

    print("=" * 50)
    print("All tests passed.")
