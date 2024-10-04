##### HELLO WORLD

from pto import run, rnd

   
#################
# INSTANCE DATA #
#################

target = "HELLO WORLD"
N = len(target) # problem size
alphabet = " ABCDEFGHIJLKLMNOPQRSTUVWXYZ"
better = max
    
######################
# SOLUTION GENERATOR #
######################

# generate a random string of letters uniformly at random
def generator(N, alphabet): # chars as list of sysbols
    return ''.join([rnd.choice(alphabet) for i in range(N)])


####################
# FITNESS FUNCTION #
####################

def fitness(string, target): # chars as list of symbols
    return sum(t == h for t, h in zip(string, target))


if __name__ == "__main__":
    (pheno, geno), fx = run(generator, fitness, 
                            gen_args=(N, alphabet), 
                            solver_args={'n_generation': 500}, 
                            fit_args=(target,), 
                            better=better)
    print(f'Solution {pheno}')
    print(f'Fitness {fx}')

