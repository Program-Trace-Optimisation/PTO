"""pto_next.trace: playing, replaying, repairing, and names."""

import random
import unittest

from pto_next import SearchSpace, current_play, play, rnd


def fine(prev, dist, rng):
    return dist.repair(prev, rng)


def by_hand():
    return [rnd.choice([0, 1], name=("x", i)) for i in range(3)]


def unnamed():
    return rnd.random()


class TestPlay(unittest.TestCase):

    def test_replay_reproduces_and_shares_choices(self):
        rng = random.Random(0)
        pheno, trace = play(by_hand, {}, rng, fine)
        pheno2, trace2 = play(by_hand, trace, rng, fine)
        self.assertEqual(pheno, pheno2)
        for a in trace:
            self.assertIs(trace2[a], trace[a])  # unchanged calls reuse the recorded choice

    def test_changed_call_is_repaired(self):
        rng = random.Random(0)
        _, trace = play(lambda: rnd.choice("abc", name="c"), {}, rng, fine)
        value = trace["c"].value
        pheno, _ = play(lambda: rnd.choice("abcd", name="c"), trace, rng, fine)
        self.assertEqual(pheno, value)  # fine repair keeps a value that is still possible

    def test_repeated_name_raises(self):
        with self.assertRaisesRegex(ValueError, "have the name"):
            play(lambda: [rnd.random(name="same") for _ in range(2)], {}, random.Random(), fine)

    def test_unnamed_call_without_naming_raises(self):
        with self.assertRaisesRegex(ValueError, "without a name"):
            play(unnamed, {}, random.Random(), fine)

    def test_current_play_is_restored(self):
        self.assertIsNone(current_play())

        def failing():
            rnd.random(name="a")
            raise RuntimeError

        with self.assertRaises(RuntimeError):
            play(failing, {}, random.Random(), fine)
        self.assertIsNone(current_play())

    def test_nested_plays(self):
        rng = random.Random(0)

        def inner():
            return rnd.random(name="inner")

        def outer():
            a = rnd.random(name="outer")
            _, t = play(inner, {}, rng, fine)
            return a, list(t)

        (a, inner_trace), trace = play(outer, {}, rng, fine)
        self.assertEqual(list(trace), ["outer"])
        self.assertEqual(inner_trace, ["inner"])


def onemax(n):
    return [rnd.choice([0, 1]) for i in range(n)]


class TestSpacesAreIndependent(unittest.TestCase):

    def test_different_configurations_coexist(self):
        lin = SearchSpace(onemax, sum, (3,), naming="linear", operators="coarse")
        dyn = SearchSpace(onemax, sum, (3,), naming="dynamic", operators="fine")
        self.assertEqual(list(lin.create_ind().geno), [0, 1, 2])
        self.assertIsInstance(next(iter(dyn.create_ind().geno)), tuple)
        self.assertEqual(list(lin.create_ind().geno), [0, 1, 2])  # unaffected by dyn

    def test_seeded_spaces_are_reproducible(self):
        a = SearchSpace(onemax, sum, (20,), seed=5)
        b = SearchSpace(onemax, sum, (20,), seed=5)
        sa, sb = a.create_ind(), b.create_ind()
        self.assertEqual(sa.pheno, sb.pheno)
        self.assertEqual(a.mutate_ind(sa).pheno, b.mutate_ind(sb).pheno)


def one_random():
    return rnd.random()


class TestRandomStreams(unittest.TestCase):

    def test_decisions_come_from_the_decision_stream(self):
        space = SearchSpace(one_random, lambda x: x, seed=7)
        self.assertEqual(space.create_ind().pheno, random.Random("7:decisions").random())

    def test_search_draws_nothing_from_the_decision_stream(self):
        space = SearchSpace(onemax, sum, (20,), seed=0)
        a, b = space.create_ind(), space.create_ind()
        before = space.decision_rng.getstate()
        for _ in range(20):  # onemax needs no new decisions after mutation or crossover
            space.mutate_position_wise_ind(a), space.mutate_point_ind(a)
            space.crossover_uniform_ind(a, b), space.crossover_one_point_ind(a, b)
        self.assertEqual(space.decision_rng.getstate(), before)

    def test_same_initial_population_whatever_the_search(self):
        from pto_next import run
        first = []
        for crossover, mutation_rate in (("crossover_uniform_ind", 0.1), ("crossover_one_point_ind", 0.9)):
            populations = []
            run(onemax, sum, (10,), Solver="genetic_algorithm", seed=3, callback=populations.append,
                solver_args={"n_generation": 3, "population_size": 6, "crossover": crossover,
                             "mutation_rate": mutation_rate})
            first.append([s.pheno for s in populations[0][0]])
        self.assertEqual(first[0], first[1])


if __name__ == "__main__":
    unittest.main()
