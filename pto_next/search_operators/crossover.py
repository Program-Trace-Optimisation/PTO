"""Crossovers: a solution made from the decisions of its parents.

The parents' traces are aligned on the addresses they share; decisions only
one parent has are kept as they are (the play uses those the child needs).
"""


def aligned(*sols):
    """The addresses in all the solutions, in the order of the first."""
    return [a for a in sols[0].geno if all(a in s.geno for s in sols[1:])]


def crossover_one_point_ind(space, sol1, sol2):
    """Aligned decisions before a random point from sol1, the rest from sol2."""
    shared = aligned(sol1, sol2)
    point = space.rng.randint(0, len(shared))
    trace = sol1.geno | sol2.geno
    trace.update((a, sol1.geno[a]) for a in shared[:point])
    return space.play(trace)


def crossover_uniform_ind(space, sol1, sol2):
    """Each aligned decision recombined from both parents."""
    cross = space.crossover_choices
    trace = sol1.geno | sol2.geno
    trace.update((a, cross(sol1.geno[a], sol2.geno[a])) for a in aligned(sol1, sol2))
    return space.play(trace)


def convex_crossover_ind(space, sol1, sol2, sol3):
    """Each aligned decision recombined from three parents (used by PSO)."""
    cross = space.convex_crossover_choices
    trace = sol1.geno | sol2.geno | sol3.geno
    trace.update((a, cross(sol1.geno[a], sol2.geno[a], sol3.geno[a])) for a in aligned(sol1, sol2, sol3))
    return space.play(trace)


OPS = (crossover_one_point_ind, crossover_uniform_ind, convex_crossover_ind)
