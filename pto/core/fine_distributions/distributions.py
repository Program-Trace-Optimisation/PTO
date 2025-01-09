from copy import copy
import random
from collections import Counter
from ..base import Dist, check_immutable
from .supp import rng_specs


class Random_real(Dist):
    """Handle continuous real-valued random variables within a range."""

    def __init__(self, fun, *args, val=None, **kwargs):
        super().__init__(fun, *args, val=val, **kwargs)
        self.min, self.max, self.range = rng_specs[fun].params(args, kwargs)

    def repair_val(self):
        self.val = min(max(self.min, self.val), self.max)

    @check_immutable
    def mutation(self):
        offspring = copy(self)
        offspring.val = self.val + random.gauss(0, 0.1 * self.range)
        offspring.repair_val()
        return offspring

    @check_immutable
    def crossover(self, other):
        if self.fun.__name__ == other.fun.__name__:
            offspring = copy(self)
            offspring.val = random.uniform(self.val, other.val)
            return offspring
        return super().crossover(other)

    @check_immutable
    def convex_crossover(self, other1, other2):
        if (
            self.fun.__name__ == other1.fun.__name__
            and self.fun.__name__ == other2.fun.__name__
        ):
            offspring = copy(self)
            min_val = min(self.val, other1.val, other2.val)
            max_val = max(self.val, other1.val, other2.val)
            offspring.val = random.uniform(min_val, max_val)
            return offspring
        return super().convex_crossover(other1, other2)

    @check_immutable
    def distance(self, other):
        if self.fun.__name__ == other.fun.__name__:
            return min(1, abs(self.val - other.val) / self.range)
        return super().distance(other)

    def size(self):
        return 10

    def repair(self, other):
        if self.fun.__name__ == other.fun.__name__:
            self.val = ((other.val - other.min) / other.range) * self.range + self.min
            self.repair_val()
        else:
            super().repair(other)


class Random_int(Dist):
    """Handle discrete integer variables with step size."""

    def __init__(self, fun, *args, val=None, **kwargs):
        super().__init__(fun, *args, val=val, **kwargs)
        self.min, self.max, self.step = rng_specs[fun].params(args, kwargs)

    def repair_val(self):
        round_val = self.min + round((self.val - self.min) / self.step) * self.step
        self.val = min(max(self.min, round_val), self.max)

    @check_immutable
    def mutation(self):
        offspring = copy(self)
        for _ in range(10):
            offspring.val = self.val + random.choice([-1, 1]) * self.step
            offspring.repair_val()
            if offspring.val != self.val:
                break
        return offspring

    @check_immutable
    def crossover(self, other):
        if self.fun.__name__ == other.fun.__name__:
            offspring = copy(self)
            min_val = min(self.val, other.val)
            max_val = max(self.val, other.val)
            offspring.val = random.randint(min_val, max_val)
            return offspring
        return super().crossover(other)

    @check_immutable
    def convex_crossover(self, other1, other2):
        if (
            self.fun.__name__ == other1.fun.__name__
            and self.fun.__name__ == other2.fun.__name__
        ):
            offspring = copy(self)
            min_val = min(self.val, other1.val, other2.val)
            max_val = max(self.val, other1.val, other2.val)
            offspring.val = random.randint(min_val, max_val)
            return offspring
        return super().convex_crossover(other1, other2)

    @check_immutable
    def distance(self, other):
        if self.fun.__name__ == other.fun.__name__:
            return min(1, abs(self.val - other.val) / (self.max - self.min))
        return super().distance(other)

    def size(self):
        return (self.max - self.min) / self.step

    def repair(self, other):
        if self.fun.__name__ == other.fun.__name__:
            self.val = ((other.val - other.min) / other.step) * self.step + self.min
            self.repair_val()
        else:
            super().repair(other)


class Random_cat(Dist):
    """Handle categorical variables from a fixed sequence."""

    def __init__(self, fun, *args, val=None, **kwargs):
        super().__init__(fun, *args, val=val, **kwargs)
        self.seq = rng_specs[fun].params(args, kwargs)

    def repair_val(self):
        if self.val not in self.seq:
            self.val = random.choice(self.seq)

    @check_immutable
    def mutation(self):
        offspring = copy(self)
        if len(set(self.seq)) >= 2:
            offspring.val = random.choice([v for v in self.seq if v != self.val])
        return offspring

    def size(self):
        return len(self.seq)

    def repair(self, other):
        if self.fun.__name__ == other.fun.__name__:
            if other.val in self.seq:
                self.val = other.val
            else:
                diff_seq = [val for val in self.seq if val not in other.seq]
                self.val = (
                    random.choice(diff_seq) if diff_seq else random.choice(self.seq)
                )
        else:
            super().repair(other)


# TODO: for the class seq, implement separate search operators
# for non-replacement (shuffle, sample) and with-replacement (choices) functions


class Random_seq(Dist):
    """Handle sequences of k unique items from a larger sequence."""

    def __init__(self, fun, *args, val=None, **kwargs):
        super().__init__(fun, *args, val=val, **kwargs)
        self.sequence, self.k = rng_specs[fun].params(args, kwargs)

    def repair_val(self):
        if not self.val or len(self.val) != self.k:
            self.val = random.sample(self.sequence, self.k)

    # point mutation (better position-wise mutation?)
    @staticmethod
    @check_immutable
    def _swap_replace_mutation(seq, pop):
        mut_seq = copy(seq)
        if random.random() < 0.5:  # swap
            if len(seq) >= 2:
                i, j = random.sample(range(len(seq)), 2)
                mut_seq[i], mut_seq[j] = seq[j], seq[i]
        else:  # replace
            idx = random.randrange(len(seq))
            if pop:
                mut_seq[idx] = random.choice(pop)
        return mut_seq

    @staticmethod
    def _multiset_diff(list1, list2):
        counter1 = Counter(list1)
        counter2 = Counter(list2)
        result = counter1 - counter2
        return list(result.elements())

    def _replace_from(self):
        return {
            "shuffle": {"pop": [], "with_repl": False},
            "sample": {
                "pop": self._multiset_diff(self.sequence, self.val),
                "with_repl": False,
            },
            "choices": {"pop": self.sequence, "with_repl": True},
        }

    @check_immutable
    def mutation(self):

        offspring = copy(self)
        offspring.val = self._swap_replace_mutation(
            self.val, self._replace_from()[self.fun.__name__]["pop"]
        )
        return offspring

    # one-point crossover (better uniform crossover?)
    @staticmethod
    @check_immutable
    def _swap_replace_crossover(seq1, seq2, pop, with_repl=True, end_point=False):
        cross_seq = copy(seq1)
        point = (
            min(len(seq1), len(seq2))
            if end_point
            else random.randrange(min(len(seq1), len(seq2)))
        )
        for i in range(point):
            if cross_seq[i] == seq2[i]:  # match
                continue
            if seq2[i] in cross_seq[i + 1 :]:  # swappable
                j = i + 1 + cross_seq[i + 1 :].index(seq2[i])
                cross_seq[i], cross_seq[j] = cross_seq[j], cross_seq[i]
            elif seq2[i] in pop:  # replaceable
                if not with_repl:
                    pop.remove(seq2[i])
                    pop.append(cross_seq[i])
                cross_seq[i] = seq2[i]
            else:  # unmatchable
                pass
        return cross_seq

    @check_immutable
    def crossover(self, other):
        if self.fun.__name__ == other.fun.__name__:
            offspring = copy(self)

            offspring.val = self._swap_replace_crossover(
                self.val, other.val, **self._replace_from()[self.fun.__name__]
            )
            return offspring

        return super().crossover(other)

    @check_immutable
    def convex_crossover(self, other1, other2):
        if (
            self.fun.__name__ == other1.fun.__name__
            and self.fun.__name__ == other2.fun.__name__
        ):
            offspring = copy(self)

            offspring.val = self._swap_replace_crossover(
                self.val, other1.val, **self._replace_from()[self.fun.__name__]
            )
            offspring.val = self._swap_replace_crossover(
                offspring.val, other2.val, **self._replace_from()[self.fun.__name__]
            )
            return offspring

        return super().convex_crossover(other1, other2)

    def _swap_distance(self, seq1, seq2):
        count = 0
        sequence = seq1.copy()

        # For each position
        for i in range(min(len(seq1), len(seq2))):
            # If element exists in sequence and isn't already in correct position
            if seq2[i] in sequence and sequence[i] != seq2[i]:
                # Find where the desired element is
                j = sequence.index(seq2[i])
                # Perform the swap
                sequence[i], sequence[j] = sequence[j], sequence[i]
                count += 1

        return count  # + abs(len(seq1)-len(seq2))

    def _swap_replace_distance(self, seq1, seq2, seq_from):
        sequence = seq1.copy()
        swaps = 0
        replacements = 0

        # For each position
        for i in range(min(len(seq1), len(seq2))):
            if sequence[i] != seq2[i]:
                # Try swap if element exists in sequence
                if seq2[i] in sequence:
                    j = sequence.index(seq2[i])
                    sequence[i], sequence[j] = sequence[j], sequence[i]
                    swaps += 1
                # Try replacement if element exists in allowed pool
                elif seq2[i] in seq_from:
                    sequence[i] = seq2[i]
                    replacements += 1

        total_distance = swaps + replacements
        return total_distance, swaps, replacements

    def _replace_distance(self, seq1, seq2, seq_from):
        replacements = 0

        # For each position
        for i in range(min(len(seq1), len(seq2))):
            # Count replacement if:
            # 1) Elements are different AND
            # 2) New element is in allowed pool
            if seq1[i] != seq2[i] and seq2[i] in seq_from:
                replacements += 1

        return replacements

    # FIXME: work in progress
    @check_immutable
    def distance(self, other):
        if self.fun.__name__ == other.fun.__name__:
            offspring = copy(self)

            # feasible crossover for shuffle is swap
            if self.fun.__name__ == "shuffle":
                dist = self._swap_distance(self.val, other.val)

            # feasible crossover for sample is swap + excluisive replace
            elif self.fun.__name__ == "sample":
                dist = self._swap_replace_distance(self.val, other.val, self.sequence)

            # feasible crossover for choices is non-exclusive replace
            else:  # self.fun.__name__ == 'choices'
                dist = self._replace_distance(self.val, other.val, self.sequence)

            return dist
        return super().distance(other)

    # FIXME
    def size(self):
        return min(len(self.sequence), self.k)

    def repair(self, other):
        if self.fun.__name__ == other.fun.__name__:

            # feasible repair for shuffle is swap
            if self.fun.__name__ == "shuffle":
                self.val = self._swap_crossover(self.val, other.val, end_point=True)

            # feasible repair for sample is swap + excluisive replace
            elif self.fun.__name__ == "sample":
                self.val = self._swap_replace_crossover(
                    self.val, other.val, self.sequence, end_point=True
                )

            # feasible repair for choices is non-exclusive replace
            else:  # self.fun.__name__ == 'choices'
                self.val = self._replace_crossover(
                    self.val, other.val, self.sequence, end_point=True
                )
        else:
            super().repair(other)
