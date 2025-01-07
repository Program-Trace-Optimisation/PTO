##### SPHERE

from pto import run, rnd

#################
# INSTANCE DATA #
#################

size = 10
better = min

######################
# SOLUTION GENERATOR #
######################


# generate a random point in the space uniformly at random
def generator(N):  # standard uniform initialisation
    return [rnd.uniform(-1, 1) for i in range(N)]


####################
# FITNESS FUNCTION #
####################


def fitness(vector):
    # target is (0.5, 0.5, ... 0.5), because some algorithms have a bias towards values such as -1, 0, or 1
    return sum([(x - 0.5) ** 2 for x in vector])


if __name__ == "__main__":
    (pheno, geno), fx = run(
        generator,
        fitness,
        gen_args=(size,),
        callback=lambda x: print(f"Hello from Solver callback! {x}"),
        better=better,
    )
    print(f"Solution {pheno}")
    print(f"Fitness {fx}")
