##### GRAMMATICAL EVOLUTION 

from pto import run, rnd

import random # for generating the problem data



    
#################
# INSTANCE DATA #
#################
    
                
### GRAMMAR
        
n_vars = 3
grammar = { 
    '<expr>'  : [['(', '<expr>', '<biop>', '<expr>', ')'], ['<var>'], ['<const>']],
    '<biop>'  : [['+'], ['-'], ['*'], ['/']],
    '<var>'   : [['x', '[', '<varidx>', ']']],
    '<varidx>': [[str(i)] for i in range(n_vars)],
    '<const>' : [['0.0'], ['0.1'], ['0.2'], ['0.3'], ['0.4'], ['0.5'], ['0.6'], ['0.7'], ['0.8'], ['0.9'], ['1.0']]
}

### TRAINING SET
        
target = lambda x: x[0] + 2*x[1]**2 + 3*x[2]**3 # target function
n = 10 # training set size
X_train = [[2*random.random() for _ in range(n_vars)] for _ in range(n)] # training inputs
y_train = [target(xi) for xi in X_train] # training outputs

better = min


        
######################
# SOLUTION GENERATOR #
######################

def generator(grammar): 

    def expand(left_sym): 
        if left_sym in grammar:
            rules = grammar[left_sym]
            selected_index = rnd.randint(0, len(rules)-1)
            return ''.join([expand(right_sym) for i, right_sym in enumerate(rules[selected_index])]) 
        else:
            return left_sym
        
    return expand('<expr>') # depth-first expansion
     
    
####################
# FITNESS FUNCTION #
####################

# fitness
def fitness(expr, X, y):
    
    # string to function
    f = eval("lambda x : " + expr)
        
    MAX_ERR = 20 * len(X)
    
    try:          
        # predictions on training set
        yhat = list(map(f, X))
    except:
        # give a large error, if an evaluation error occurs (e.g., division by 0)
        err = MAX_ERR
    else:
        # error on training set (when no evaluation error)
        err = min(MAX_ERR, sum(abs(yi - yhati) for yi, yhati in zip(y, yhat)))
            
    return err 

if __name__ == '__main__':
    (pheno, geno), fx = run(generator, fitness, gen_args=(grammar,), fit_args=(X_train, y_train), better=better)
    print(f'Solution {pheno}')
    print(f'Fitness {fx}')
