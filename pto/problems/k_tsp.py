##### k-TSP

# k-TSP:  Given a set of n cities and a fixed value 1 < k ≤ n, the k-TSP is to find a minimum length tour by visiting exactly k of the n cities
# https://www.sciencedirect.com/science/article/pii/S1877050918320714#:~:text=Abstract,k%20of%20the%20n%20cities

from pto import run, rnd

import random  # for generating random problem instances


#################
# INSTANCE DATA #
#################

N = 15  # problem size: number of cities
k = 5   # number of cities to visit

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
def generator_native(N, k): 
    # relies on new native PTO machinery - nothing special needed in the generator
    L = list(range(N))
    return rnd.sample(L, k) # sample returns an ordered subset without replacement

def generator_sim_knuth(N, k):
    def _sample(L, k):
        L = L[:]
        n = len(L)
        for i in range(k):
            j = rnd.randrange(i, n)
            L[i], L[j] = L[j], L[i]
        return L[:k]
    L = list(range(N))
    return _sample(L, k)

def generator_sim_remove(N, k):
    def _sample(L, k):
        M = []
        L = L[:] # removing items in the loop causes problems otherwise - a nasty "gotcha" in "old" PTO, pre-Jan 2025
        for _ in range(k):
            el = rnd.choice(L)
            L.remove(el)
            M.append(el)
        return M
    L = list(range(N))
    return _sample(L, k)


#####################
# DEFAULT GENERATOR #
#####################

# the "obvious" generator, suitable for PTO with custom
# distributions for shuffle, choices, and sample.
generator = generator_native 



####################
# FITNESS FUNCTION #
####################


def fitness(x, k, dist):
    # N is irrelevant to fitness
    K = len(x)
    # k is the k-TSP problem parameter, K is the length of the provided solution, they should be equal
    assert k == K 
    return sum(dist[x[i]][x[(i + 1) % K]] for i in range(K))


if __name__ == "__main__":
    dist = make_problem_data(N, random_state=0)
    generators = [generator_native, generator_sim_knuth, generator_sim_remove]
    for generator in generators:
        print(generator.__name__)
        (pheno, geno), fx, history = run(
            generator,
            fitness,
            gen_args=(N, k),
            fit_args=(k, dist),
            better=better,
            Solver="genetic_algorithm",
            solver_args={"n_generation": 30, "return_history": True},
        )
        print(f"Solution {pheno}")
        print(f"Fitness {fx}")
        print(history[-10:])
