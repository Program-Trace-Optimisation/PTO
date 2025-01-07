##### TSP

from pto import run, rnd

import random  # for generating random problem instances


#################
# INSTANCE DATA #
#################

N = 15  # problem size

# distance matrix generated at random (we could use rnd.random() instead of random.random() as this is not traced)
# TODO I think the above comment should say we could NOT use??


def make_problem_data(N, random_state=None):
    if random_state is not None:
        random.seed(
            random_state
        )  # notice we use Python random as normal for problem data, not PTO rnd
    return [[random.random() for _ in range(N)] for _ in range(N)]


better = min

######################
# SOLUTION GENERATOR #
######################


# generate a random permutation uniformly at random
# we cannot use rnd.shuffle() directly - it has to do with mutable arguments
# and wanting mutation to behave well - it is a long story
# TODO document this properly.
# so, we use the Knuth shuffle
def generator(N):
    perm = list(range(N))

    for i in range(N):
        j = rnd.choice(
            range(i, N)
        )  # NB, not randint(i, N-1) as that treats the result as an ordinal
        perm[j], perm[i] = perm[i], perm[j]  # swap

    return perm


####################
# FITNESS FUNCTION #
####################


def fitness(x, dist):
    N = len(x)
    return sum(dist[x[i]][x[(i + 1) % N]] for i in range(N))


if __name__ == "__main__":
    dist = make_problem_data(N, random_state=0)
    (pheno, geno), fx, history = run(
        generator,
        fitness,
        gen_args=(N,),
        fit_args=(dist,),
        better=better,
        Solver="genetic_algorithm",
        solver_args={"n_generation": 30, "return_history": True},
    )
    print(f"Solution {pheno}")
    print(f"Fitness {fx}")
    print(history[-10:])
