"""Mutations: a solution changed by changing some of its decisions."""


def mutate_point_ind(space, sol):
    """Mutate one random decision."""
    if not sol.geno:
        return space.play({})
    trace = dict(sol.geno)
    address = space.search_rng.choice(list(trace))
    trace[address] = space.mutate_choice(trace[address])
    return space.play(trace)


def mutate_position_wise_ind(space, sol):
    """Mutate each decision with probability 1/length."""
    if not sol.geno:
        return space.play({})
    p, rng, mutate = 1.0 / len(sol.geno), space.search_rng, space.mutate_choice
    return space.play({a: mutate(c) if rng.random() < p else c for a, c in sol.geno.items()})


def mutate_random_ind(space, sol):
    """A new random solution."""
    return space.play({})


OPS = (mutate_point_ind, mutate_position_wise_ind, mutate_random_ind)
