from collections import namedtuple
from copy import copy
import random
import math

from .check_immutable import check_immutable
from .tracer import tracer

# Solution data structure
Sol = namedtuple("Sol", ["pheno", "geno"])


class Op:
    """
    Evolutionary operators that work on traced sequences of stochastic operations.

    This class implements standard evolutionary algorithm operators (mutation, crossover)
    that operate on solutions represented as traces of random operations. Each solution
    consists of a phenotype (observable characteristics) and genotype (trace of operations).

    Attributes:
        generator: Problem-specific function that generates solutions
        fitness: Problem-specific function that evaluates solutions
        mutate_ind: Selected mutation operator
        crossover_ind: Selected crossover operator
        tracer: Mechanism to record and replay sequences of operations
    """

    tracer = tracer  # bind operators to tracer

    def __init__(
        self,
        generator=None,
        fitness=None,
        mutation="mutate_point_ind",
        crossover="crossover_uniform_ind",
        tracer=tracer,
    ):
        """
        Initialize operator with problem-specific functions and selected variation operators.

        Args:
            generator: Function that generates new solutions
            fitness: Function that evaluates solution quality
            mutation: Name of mutation operator to use
            crossover: Name of crossover operator to use
            tracer: Tracer instance for recording operations
        """
        self.generator = generator
        self.fitness = fitness
        self.mutate_ind = getattr(self, mutation)
        self.crossover_ind = getattr(self, crossover)

    def __repr__(self):
        """Create string representation showing configured functions and operators."""
        gen_name = None if self.generator is None else self.generator.__name__
        fit_name = None if self.fitness is None else self.fitness.__name__
        return f"{self.__class__.__name__}({gen_name}, {fit_name}, {self.mutate_ind.__name__}, {self.crossover_ind.__name__})"

    def evaluate_ind(self, sol):
        """Evaluate fitness of a solution's phenotype."""
        return self.fitness(sol.pheno)

    def create_ind(self):
        """Create new individual by running generator with empty trace."""
        pheno, geno = Op.tracer.play(self.generator, {})
        return Sol(pheno, geno)

    def fix_ind(self, geno):
        """
        Repair/validate genotype by replaying through generator.

        Args:
            geno: Genotype (trace) to repair

        Returns:
            Sol: Valid solution with repaired genotype and corresponding phenotype
        """
        pheno, repaired_geno = Op.tracer.play(self.generator, geno)
        return Sol(pheno, repaired_geno)

    @check_immutable
    def mutate_position_wise_ind(self, sol):
        """
        Mutate each position in genotype with probability 1/length.

        Args:
            sol: Solution to mutate

        Returns:
            Sol: New mutated solution
        """
        mut_prob = 1.0 / len(sol.geno)
        new_geno = {
            name: entry.mutation() if random.random() <= mut_prob else entry
            for name, entry in sol.geno.items()
        }
        return self.fix_ind(new_geno)

    @check_immutable
    def mutate_point_ind(self, sol):
        """
        Mutate single random position in genotype.

        Args:
            sol: Solution to mutate

        Returns:
            Sol: New solution with one mutated position
        """
        new_geno = copy(sol.geno)
        name = random.choice(list(new_geno.keys()))
        new_geno[name] = new_geno[name].mutation()
        return self.fix_ind(new_geno)

    @check_immutable
    def mutate_random_ind(self, _):
        """Create completely new random solution."""
        return self.create_ind()

    @check_immutable
    def crossover_one_point_ind(self, sol1, sol2):
        """
        Perform one-point crossover between two solutions.

        Args:
            sol1, sol2: Parent solutions to recombine

        Returns:
            Sol: New solution combining parts of both parents
        """
        alignment = self._align_genotypes(sol1, sol2)
        crossover_point = random.randint(0, len(alignment))
        new_geno_alignment = {
            key: (sol1 if pos <= crossover_point else sol2).geno[key]
            for pos, key in enumerate(alignment)
        }
        new_geno = sol1.geno | sol2.geno | new_geno_alignment
        return self.fix_ind(new_geno)

    @check_immutable
    def crossover_uniform_ind(self, sol1, sol2):
        """
        Perform uniform crossover between two solutions.

        For each aligned position, randomly select from either parent.

        Args:
            sol1, sol2: Parent solutions to recombine

        Returns:
            Sol: New solution with uniformly mixed parent traits
        """
        alignment = self._align_genotypes(sol1, sol2)
        new_geno_alignment = {
            key: sol1.geno[key].crossover(sol2.geno[key]) for key in alignment
        }
        new_geno = sol1.geno | sol2.geno | new_geno_alignment
        return self.fix_ind(new_geno)

    @check_immutable
    def convex_crossover_ind(self, sol1, sol2, sol3):
        """
        Perform three-parent convex crossover.

        Args:
            sol1, sol2, sol3: Parent solutions to recombine

        Returns:
            Sol: New solution combining traits from three parents
        """
        alignment = self._align_genotypes(sol1, sol2, sol3)
        new_geno_alignment = {
            key: sol1.geno[key].convex_crossover(sol2.geno[key], sol3.geno[key])
            for key in alignment
        }
        new_geno = sol1.geno | sol2.geno | sol3.geno | new_geno_alignment
        return self.fix_ind(new_geno)

    @staticmethod
    def _align_genotypes(*sols):
        """
        Find common keys across solutions maintaining order from first solution.

        When debug mode is active, verifies that common keys appear in same order
        across all solutions.

        Args:
            *sols: Solutions to align

        Returns:
            list: Ordered list of keys common to all solutions

        Raises:
            AssertionError: In debug mode, if common keys are in different orders
        """
        base_keys = list(sols[0].geno.keys())
        alignment = [key for key in base_keys if all(key in sol.geno for sol in sols)]

        if __debug__:  # Only check alignment consistency in debug mode
            for sol in sols[1:]:
                sol_alignment = [key for key in sol.geno.keys() if key in alignment]
                assert (
                    sol_alignment == alignment
                ), "PTO: common keys in different orders!"

        return alignment

    @check_immutable
    def distance_ind(self, sol1, sol2):
        """
        Compute distance between two solutions.

        Distance combines differences in aligned values and structural differences
        in genotype keys.

        Args:
            sol1, sol2: Solutions to compare

        Returns:
            float: Distance measure between solutions
        """
        common = set(sol1.geno.keys()) & set(sol2.geno.keys())
        distance_alignment = sum(
            sol1.geno[key].distance(sol2.geno[key]) for key in common
        )
        symmetric_difference = len(set(sol1.geno.keys()) ^ set(sol2.geno.keys()))
        return distance_alignment + symmetric_difference

    def space_dimension_ind(self, sol):
        """
        Compute dimension of solution space based on genotype sizes.

        Args:
            sol: Solution to analyze

        Returns:
            float: Log2 sum of genotype entry sizes
        """
        return sum(math.log2(entry.size()) for _, entry in sol.geno.items())
