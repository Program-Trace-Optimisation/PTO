"""An example of a new search operator module, as it would be added to
pto_next/search_operators/ (the README shows it)."""


def mutate_two_points_ind(space, sol):
    """Mutate two different random decisions (one if there is only one)."""
    trace = dict(sol.geno)
    for address in space.rng.sample(list(trace), min(2, len(trace))):
        trace[address] = space.mutate_choice(trace[address])
    return space.play(trace)


OPS = (mutate_two_points_ind,)
