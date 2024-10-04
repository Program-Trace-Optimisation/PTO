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
def generator(N): #standard uniform initialisation 
    return [rnd.uniform(-1, 1) for i in range(N)]
    
####################
# FITNESS FUNCTION #
####################

def fitness(vector): 
    return sum([x**2 for x in vector])   

if __name__ == "__main__":
    (pheno, geno), fx = run(generator, fitness, 
                            gen_args=(size,), 
                            callback=lambda x: print(f"Hello from Solver callback! {x}"),
                            better=better)
    print(f'Solution {pheno}')
    print(f'Fitness {fx}')