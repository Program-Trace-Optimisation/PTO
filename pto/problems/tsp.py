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



##########################
# ALTERNATIVE GENERATORS #
##########################

# Several alternative generators for experiments re the new distributions for shuffle, choices, and sample.
def generator_native(N): 
    # relies on new native PTO machinery - nothing special needed in the generator
    x = list(range(N))
    rnd.shuffle(x)
    return x

def generator_knuth(N):
    def _shuffle(L):
        for i in range(N):
            j = rnd.choice(
                range(i, N)
            )  # NB, not randint(i, N-1) as that treats the result as an ordinal
            L[j], L[i] = L[i], L[j]  # swap       
    x = list(range(N))
    _shuffle(x)
    return x

def generator_pmx(N):
    # in-place on L, but a more "naive" shuffle, 
    # more disruptive, giving PMX-like crossover
    x = list(range(N))
    y = []
    while len(x):
        n = rnd.choice(x)
        y.append(n)
        x.remove(n)
    return y


#####################
# DEFAULT GENERATOR #
#####################

# the "obvious" generator, suitable for PTO with custom
# distributions for shuffle, choices, and sample.
generator = generator_native 



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
