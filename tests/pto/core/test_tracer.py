"""Tests for the base Tracer and the core package interfaces."""

import random
import unittest

from pto.core.base import Tracer, Dist


class TestTracer(unittest.TestCase):

    def test_play_records_and_replays(self):
        tracer = Tracer()

        def gen():
            return [tracer.sample(i, Dist(random.random)) for i in range(3)]

        sol, trace = tracer.play(gen, {})
        self.assertEqual(list(trace), [0, 1, 2])
        sol2, _ = tracer.play(gen, trace)
        self.assertEqual(sol, sol2)

    def test_duplicate_name_raises_and_deactivates(self):
        tracer = Tracer()

        def gen():
            tracer.sample("x", Dist(random.random))
            tracer.sample("x", Dist(random.random))

        with self.assertRaisesRegex(ValueError, "not unique"):
            tracer.play(gen, {})
        self.assertFalse(tracer.active)


class TestStarImports(unittest.TestCase):

    def test_star_imports(self):
        for module in ["pto.core.base", "pto.core.fine_distributions",
                       "pto.core.automatic_names"]:
            with self.subTest(module=module):
                exec(f"from {module} import *", {})


if __name__ == "__main__":
    unittest.main()
