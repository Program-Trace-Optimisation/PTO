##### ONEMAX

from pto import run, rnd


#################
# INSTANCE DATA #
#################

size = 10
better = max  # maximisation problem, not minimisation


######################
# SOLUTION GENERATOR #
######################


# generate a random binary string uniformly at random
def generator(size):
    return [rnd.choice([0, 1]) for i in range(size)]


####################
# FITNESS FUNCTION #
####################

fitness = sum


if __name__ == "__main__":
    (pheno, geno), fx = run(generator, fitness, gen_args=(size,), better=better)
    print(f"Solution {pheno}")
    print(f"Fitness {fx}")
