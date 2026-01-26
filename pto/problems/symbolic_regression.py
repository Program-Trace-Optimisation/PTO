# SYMBOLIC REGRESSION

from pto import run, rnd

import random  # for generating problem data
import math


#################
# INSTANCE DATA #
#################


def full(func_set, term_set): # used to generate a target for a particular problem instance
    max_depth = 1 + math.ceil(math.log2(
        len(term_set)
    ))  
    # estimate required depth. imperfect because we have 'not'
    # note, same formula as in the sr_depth_gen PTO generator, in as_classes.py

    def _full(depth):
        if depth >= max_depth:
            expr = random.choice(
                term_set
            )  # use random, not rnd, as this is for creation of problem instance
        else:
            func, arity = random.choice(func_set)
            if arity == 1:
                expr = "(%s %s)" % (func, _full(depth + 1))
            else:  # arity = 2
                expr = "(%s %s %s)" % (_full(depth + 1), func, _full(depth + 1))
        return expr

    return _full(0)

def even_parity(s):
    """
    Generate even-parity function on s boolean variables.
    Returns True if an even number of variables are True, False otherwise.

    For s variables, this is: XOR of all variables
    Example for s=3: x[0] ^ x[1] ^ x[2]
    """
    return "sum(x) % 2 == 0"


def cnf_generator(s, clause_len):
    # an alternative target generator
    # we have s variables, and we combine them in cnf
    # we have s / clause_len clauses
    # each term of length clause_len
    assert s % clause_len == 0
    terms = []
    for i in range(0, s, clause_len):
        vs = (f"{'not ' if j % 2 == 1 else ''}x[{j}]" for j in range(i, i+clause_len))
        st = f'({" and ".join(vs)})'
        terms.append(st)
    expr = " or ".join(terms)
    # print(expr)
    return expr

def make_training_data(n_samples, n_vars, func_set, term_set, target_gen=cnf_generator, cnf_clause_len=None):
    # pass in target_gen='full' if we want a "full" target instead, or target_gen='even_parity'

    if target_gen == cnf_generator:
        target_str = cnf_generator(n_vars, cnf_clause_len)
    elif target_gen == full:
        target_str = full(func_set, term_set)
    elif target_gen == even_parity:
        target_str = even_parity(n_vars)
    else:
        raise ValueError("Unexpected target generator", target_gen)

    target = eval("lambda x: " + target_str)
    X = [
        [random.choice([False, True]) for _ in range(n_vars)] for _ in range(n_samples)
    ]  # training inputs
    y = [target(xi) for xi in X]  # training outputs
    return X, y, target_str

def make_critical_training_data_cnf(n_vars, clause_len):
    """
    Generate critical test cases properly isolating each clause.
    """
    assert n_vars % clause_len == 0

    target_str = cnf_generator(n_vars, clause_len)
    target = eval("lambda x: " + target_str)

    X = []
    y = []

    n_clauses = n_vars // clause_len

    # Helper: pattern that makes ALL clauses FALSE
    def all_false_pattern():
        x = []
        for var_idx in range(n_vars):
            if var_idx % 2 == 0:
                x.append(False)  # Even: need False (positive literal)
            else:
                x.append(True)   # Odd: need True (to make NOT False)
        return x

    # Test 1: Pattern where ALL clauses are FALSE
    x_all_false = all_false_pattern()
    X.append(x_all_false)
    y.append(target(x_all_false))

    # For each clause: test it being TRUE (others FALSE)
    for clause_idx in range(n_clauses):
        start_var = clause_idx * clause_len

        # Start with all-false pattern
        x_clause_true = all_false_pattern()

        # Activate THIS clause by setting its variables correctly
        for offset in range(clause_len):
            var_idx = start_var + offset
            if var_idx % 2 == 0:
                x_clause_true[var_idx] = True  # Even: positive literal needs True
            else:
                x_clause_true[var_idx] = False  # Odd: negated literal needs False

        X.append(x_clause_true)
        y.append(target(x_clause_true))

        # Test each variable in this clause being wrong
        for offset in range(clause_len):
            x_var_wrong = all_false_pattern()

            # Set all variables in this clause correct EXCEPT one
            for off in range(clause_len):
                var_idx = start_var + off
                if off != offset:  # Don't fix the one we're testing
                    if var_idx % 2 == 0:
                        x_var_wrong[var_idx] = True
                    else:
                        x_var_wrong[var_idx] = False

            X.append(x_var_wrong)
            y.append(target(x_var_wrong))

    # Edge cases
    X.append([True] * n_vars)
    y.append(target([True] * n_vars))

    X.append([False] * n_vars)
    y.append(target([False] * n_vars))

    # Remove duplicates
    unique_cases = {}
    for i, x in enumerate(X):
        x_tuple = tuple(x)
        if x_tuple not in unique_cases:
            unique_cases[x_tuple] = y[i]

    X_unique = [list(x_tuple) for x_tuple in unique_cases.keys()]
    y_unique = list(unique_cases.values())

    return X_unique, y_unique, target_str


better = min





######################
# SOLUTION GENERATOR #
######################


# generate random expression
def generator(func_set, term_set, max_depth=6):

    def rnd_expr(depth):  # Growth Initialisation
        if depth <= 0 or rnd.random() < len(term_set) / (len(term_set) + len(func_set)):
            expr = rnd.choice(term_set)
        else:
            func, arity = rnd.choice(func_set)
            if arity == 1:
                expr = "(%s %s)" % (func, rnd_expr(depth - 1))
            else:  # arity = 2
                expr = "(%s %s %s)" % (rnd_expr(depth - 1), func, rnd_expr(depth - 1))
        return expr

    return rnd_expr(max_depth)


# generate random expression: avoid too many trivial-sized trees
def generator_depth(func_set, term_set, max_depth=6):

    def rnd_expr(depth):  # Growth Initialisation
        if depth <= 0 or rnd.random() < 1.0 / depth: 
            expr = rnd.choice(term_set)
        else:
            func, arity = rnd.choice(func_set)
            if arity == 1:
                expr = "(%s %s)" % (func, rnd_expr(depth - 1))
            else:  # arity = 2
                expr = "(%s %s %s)" % (rnd_expr(depth - 1), func, rnd_expr(depth - 1))
        return expr

    return rnd_expr(max_depth)


####################
# FITNESS FUNCTION #
####################


# fitness
def fitness(expr, X, y, target_str=None):

    # the user must pass X and y, which may eg have been generated using make_training_data
    # target_str is optional and is unused, but the benefit of allowing it here
    # is that it is stored as part of fit_args, which can then be queried and saved at run time

    # string to function
    f = eval("lambda x: " + expr)

    # predictions on traning set
    yhat = [f(xi) for xi in X]

    # error on traing set
    err = sum(abs(yhati - yi) for (yhati, yi) in zip(yhat, y))

    return err


def balanced_fitness(expr, X, y, target_str=None):
    """
    Fitness function using balanced error rate.
    Returns value in [0, 1] where:
    - 0.0 = perfect classification
    - 0.5 = random baseline
    - 1.0 = worst possible
    """
    f = eval("lambda x: " + expr)
    yhat = [f(xi) for xi in X]

    # Separate by class
    true_indices = [i for i, yi in enumerate(y) if yi == True]
    false_indices = [i for i, yi in enumerate(y) if yi == False]

    # Handle edge cases
    if len(true_indices) == 0 or len(false_indices) == 0:
        err = sum(abs(yhati - yi) for (yhati, yi) in zip(yhat, y))
        return err / len(y)

    # Error rate per class
    true_error_rate = sum(1 for i in true_indices if yhat[i] != y[i]) / len(true_indices)
    false_error_rate = sum(1 for i in false_indices if yhat[i] != y[i]) / len(false_indices)

    # Balanced error: average of both
    return (true_error_rate + false_error_rate) / 2


if __name__ == "__main__":

    n_vars = 9  # problem size (number of input variables)
    func_set = [("and", 2), ("or", 2), ("not", 1)]  # functions set
    term_set = [f"x[{i}]" for i in range(n_vars)]  # terminals set

    # create training set
    n_samples = n_vars * 10  # training set size
    X_train, y_train, target = make_training_data(n_samples, n_vars, func_set, term_set, cnf_generator)

    (pheno, geno), fx = run(
        generator,
        fitness,
        gen_args=(func_set, term_set),
        fit_args=(X_train, y_train),
        better=better,
        Solver="particle_swarm_optimisation",
        solver_args={"n_iteration": 100},
    )
    print(f"Target {target}")
    print(f"Solution {pheno}")
    print(f"Fitness {fx}")
