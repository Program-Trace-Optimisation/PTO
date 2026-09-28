"""Distances between solutions."""


def distance_ind(space, sol1, sol2):
    """Sum of the distances of shared decisions, plus 1 per decision only one has."""
    g1, g2 = sol1.geno, sol2.geno
    dist = space.distance_choices
    shared = sum(dist(g1[a], g2[a]) for a in g1 if a in g2)
    return shared + sum(a not in g2 for a in g1) + sum(a not in g1 for a in g2)


OPS = (distance_ind,)
