# SYMBOLIC REGRESSION

from pto import run, rnd

import random # for generating problem data
import math

    
#################
# INSTANCE DATA #
#################

def make_training_data(n_samples, n_vars, func_set, term_set):
    target_str = full(func_set, term_set) # target function: use a large subset of the variables
    # print(target_str)
    target = eval("lambda x: " + target_str)
    X = [[random.choice([0, 1]) for _ in range(n_vars)] for _ in range(n_samples)] # training inputs
    y = [target(xi) for xi in X] # training outputs
    return X, y

better = min
        
def full(func_set, term_set):
    max_depth = math.log2(len(term_set)) # estimate required depth. imperfect because we have 'not'
    def _full(depth):
        if depth >= max_depth:
            expr = random.choice(term_set) # use random as this is for creation of problem instance
        else:
            func, arity = random.choice(func_set)
            if arity == 1:
                expr = '(%s %s)' % (func, _full(depth + 1))
            else: # arity = 2
                expr = '(%s %s %s)' % (_full(depth + 1), func, _full(depth + 1))
        return expr
    return _full(0)

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
    f = eval("lambda x: " + expr)
    
    # predictions on traning set
    yhat = [f(xi) for xi in X] 
    
    # error on traing set
    err = sum(abs(yhati - yi) for (yhati, yi) in zip(yhat, y))
    
    return err



if __name__ == '__main__':

    n_vars = 10 # problem size (number of input variables)
    func_set = [('and', 2), ('or', 2), ('not', 1)] # functions set
    term_set = [f'x[{i}]' for i in range(n_vars)] # terminals set

    # create training set
    n_samples = 10 # training set size
    X_train, y_train = make_training_data(n_samples, n_vars, func_set, term_set)

    (pheno, geno), fx = run(generator, fitness, 
                            gen_args=(func_set, term_set), 
                            fit_args=(X_train, y_train), better=better)
    print(f'Solution {pheno}')
    print(f'Fitness {fx}')