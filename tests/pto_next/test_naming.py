"""pto_next.naming: linear, dynamic and static addresses."""

import unittest

from pto import rnd as old_rnd
from pto_next import SearchSpace, format_address, rnd
from pto_next import rnd as random_alias
from pto_next.naming import StaticNamingError


# generators covering the scopes; dynamic and static must give the same addresses

def g_nested():
    def helper(k):
        return rnd.choice([0, 1]) + rnd.randint(0, k)
    return [helper(i) for i in range(3)], helper(5) + helper(6)


def g_loops():
    total = []
    for i in range(3):
        if i == 1:
            continue
        total.append(rnd.random())
    j = 0
    while j < 4:
        j += 1
        if j % 2:
            continue  # the iteration count must not stall
        total.append(rnd.random())
    for k in range(2):
        pass
    else:
        total.append(rnd.random())
    return total


def g_recursive():
    def tree(depth):
        if depth == 0 or rnd.random() < 0.3:
            return rnd.choice("xy")
        return [rnd.choice("+*"), tree(depth - 1), tree(depth - 1)]
    return tree(4)


def g_comprehensions():
    xs = [rnd.random() for i in range(rnd.randint(1, 3))]  # rnd in the iterable
    pairs = {(i, j): rnd.choice("ab") for i in range(2) for j in range(2) if rnd.random() < 2}
    return xs, pairs, sum(rnd.random() for _ in range(2))


def g_def_in_block():
    if True:
        def helper():
            return rnd.random()
    return [helper() for i in range(2)]


def g_alias():
    return [random_alias.choice([0, 1]) for i in range(3)]


def g_old_rnd():
    return [old_rnd.choice([0, 1]) for i in range(3)]


def g_explicit_name():
    return rnd.random(name="mine"), rnd.random()


def outside_helper():
    return rnd.choice([0, 1])


def g_outside_helper():
    return [outside_helper(), outside_helper()], [outside_helper() for i in range(2)]


def g_function_as_value():
    def helper(x):
        return rnd.random() + x
    return list(map(helper, [1]))


GENERATORS = [g_nested, g_loops, g_recursive, g_comprehensions, g_def_in_block, g_alias,
              g_old_rnd, g_explicit_name]


def trace(generator, naming, seed=0):
    return SearchSpace(generator, lambda x: 0, naming=naming, seed=seed).create_ind()


class TestStructuredNames(unittest.TestCase):

    def test_dynamic_and_static_agree(self):
        for g in GENERATORS:
            for seed in range(5):
                with self.subTest(generator=g.__name__, seed=seed):
                    d, s = trace(g, "dynamic", seed), trace(g, "static", seed)
                    self.assertEqual(list(d.geno), list(s.geno))
                    self.assertEqual(d.pheno, s.pheno)

    def test_replay_reproduces(self):
        for g in GENERATORS:
            for naming in ("linear", "dynamic", "static"):
                with self.subTest(generator=g.__name__, naming=naming):
                    space = SearchSpace(g, lambda x: 0, naming=naming, seed=1)
                    sol = space.create_ind()
                    self.assertEqual(space.play(sol.geno), sol)

    def test_address_format(self):
        geno = trace(g_nested, "dynamic").geno
        self.assertEqual(format_address(next(iter(geno))), "comp@4.31:0/helper@4.12/choice@3.15")

    def test_loop_iterations(self):
        names = [format_address(a) for a in trace(g_loops, "static").geno]
        self.assertEqual(names, ["for@3.4:0/random@6.21", "for@3.4:2/random@6.21",
                                 "while@8.4:1/random@12.21", "while@8.4:3/random@12.21",
                                 "for@13.4:1/random@16.21"])

    def test_explicit_name_is_kept(self):
        self.assertIn("mine", trace(g_explicit_name, "static").geno)

    def test_old_rnd_is_replaced(self):
        self.assertEqual(len(trace(g_old_rnd, "dynamic").geno), 3)
        self.assertEqual(len(trace(g_old_rnd, "linear").geno), 3)


class TestLimits(unittest.TestCase):

    def test_dynamic_names_helpers_defined_elsewhere(self):
        sol = trace(g_outside_helper, "dynamic")
        self.assertEqual(len(sol.geno), 4)
        self.assertTrue(all("outside_helper@" in format_address(a) for a in sol.geno))

    def test_static_rejects_helpers_defined_elsewhere(self):
        with self.assertRaisesRegex(ValueError, "naming='dynamic'"):
            trace(g_outside_helper, "static")

    def test_static_rejects_nested_function_used_as_value(self):
        with self.assertRaises(StaticNamingError):
            trace(g_function_as_value, "static")
        self.assertEqual(len(trace(g_function_as_value, "dynamic").geno), 1)

    def test_lambda_needs_linear_naming(self):
        gen = lambda: rnd.random()  # noqa: E731
        with self.assertRaises(ValueError):
            trace(gen, "dynamic")
        self.assertEqual(list(trace(gen, "linear").geno), [0])

    def test_nested_generator_uses_enclosing_variables(self):
        n = 4

        def local_generator():
            return [rnd.random() for i in range(n)]

        for naming in ("linear", "dynamic", "static"):
            self.assertEqual(len(trace(local_generator, naming).geno), n)


if __name__ == "__main__":
    unittest.main()
