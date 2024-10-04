
##### MATRIX EVOLUTION


from pto import run, rnd

    
#################
# INSTANCE DATA #
#################
            
N = 5 # problem size
                
# target graph:
# 0 - 1
# |   |
# 3 - 2 
target = [[0, 1, 0, 1],
          [1, 0, 1, 0],
          [0, 1, 0, 1],
          [1, 0, 1, 0]]
        
better = min

        
######################
# SOLUTION GENERATOR #
######################

# uniformly choose a size, up to max size N
# then generate a uniform random binary matrix
def generator(N):
    size = rnd.randint(1, N)
    return [[rnd.choice([0,1]) for i in range(size)] 
            for j in range(size)]


####################
# FITNESS FUNCTION #
####################

def fitness(sol, target):
    m1, m2 = ((sol, target) if len(sol) <= len(target) else (target, sol))
    l1, l2 = len(m1), len(m2)
    #diff=0
    #for i in range(l2):
    #    for j in range(l2):
    #        if i<l1 and j<l1: 
    #            diff += m1[i][j]!=m2[i][j]
    #        else
    #            diff += 1
    diff = sum(m1[i][j] != m2[i][j] if i < l1 and j < l1 else 1 
               for i in range(l2) 
               for j in range(l2))
    return diff
    

if __name__ == '__main__':
    (pheno, geno), fx = run(generator, fitness, 
                            gen_args=(N,), 
                            fit_args=(target,), better=better)
    print(f'Solution {pheno}')
    print(f'Fitness {fx}')