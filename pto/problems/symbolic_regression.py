# SYMBOLIC REGRESSION

from pto import run, rnd

import random # for generating problem data

    
#################
# INSTANCE DATA #
#################
    
                
n_vars = 3 # problem size (number of input variables)
        
func_set = [('and', 2), ('or', 2), ('not', 1)] # functions set
term_set = ['x1', 'x2', 'x3'] # terminals set
        
target = lambda x1, x2, x3: x1 or x2 or not x3 # target function
    
# create training set
n = 10 # training set size
X_train = [[random.choice([0, 1]) for _ in range(3)] for _ in range(n)] # training inputs
y_train = [target(*xi) for xi in X_train] # training outputs

better = min
        

######################
# SOLUTION GENERATOR #
######################

# generate random expression
def generator(func_set, term_set): 

    def rnd_expr(): # Growth Initialisation
        if rnd.random() < len(term_set)/(len(term_set)+len(func_set)):
            expr = rnd.choice(term_set)
        else:
            func, arity = rnd.choice(func_set)
            if arity == 1:
                expr = '(%s %s)' % (func, rnd_expr())
            else: # arity = 2
                expr = '(%s %s %s)' % (rnd_expr(), func, rnd_expr())
        return expr
        
    return rnd_expr()


####################
# FITNESS FUNCTION #
####################

# fitness
def fitness(expr, X, y):
    
    # string to function
    f = eval("lambda x1, x2, x3 : " + expr)
    
    # predictions on traning set
    yhat = [f(*xi) for xi in X] 
    
    # error on traing set
    err = sum(abs(yhati - yi) for (yhati, yi) in zip(yhat, y))
    
    return err



if __name__ == '__main__':
    (pheno, geno), fx = run(generator, fitness, 
                            gen_args=(func_set, term_set), 
                            fit_args=(X_train, y_train), better=better)
    print(f'Solution {pheno}')
    print(f'Fitness {fx}')