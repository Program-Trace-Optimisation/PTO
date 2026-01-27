#!/usr/bin/env python3
"""
Lambda Calculus Representation with Program Trace Optimization
- Uses tuple representation with macros for combinators
- Provides generators, evaluators, and fitness functions for PTO
"""

from itertools import count
from statistics import mean
from pto import rnd as random


from lc import *


# Add this global counter at the top of the file
fitness_call_count = 0
fitness_exception_count = 0

# GENERATOR - Tuple reresentation with MACROS (used as combinators)

def tuple_generator():
    """Generate random lambda calculus terms with or without macros"""
    global MAX_DEPTH, MACROS_ENABLED
    
    fresh_var_gen = make_fresh_var_gen()

    def term_gen(scope, depth):
        """Generate a term with given variable scope and maximum depth"""
        if scope:
            choices = ['var', 'abs', 'app'] if depth > 0 else ['var']
        else:
            choices = ['abs', 'abs', 'app']

        if MACROS_ENABLED:
            choices.append('mac')
        
        match random.choice(choices):
            case 'var':
                return ('var', random.choice(scope))
            case 'abs':
                var = next(fresh_var_gen)
                body = term_gen(scope + [var], depth - 1)
                return ('abs', var, body)
            case 'app':
                func = term_gen(scope, depth - 1)
                arg = term_gen(scope, depth - 1)
                return ('app', func, arg)
            case 'mac':
                return random.choice(MACROS)

    return term_gen([], MAX_DEPTH)


def debruijn_to_names(term):
   def convert(term, var_count, depth=0):
       match term:
           case ('var', index):
               # Convert de Bruijn index to variable name based on depth
               return ('var', f'x{depth - index}')
           case ('abs', body):
               # Increment depth and var_count for body
               return ('abs', f'x{var_count + 1}',
                      convert(body, var_count + 1, depth + 1))
           case ('app', func, arg):
               return ('app',
                      convert(func, var_count, depth),
                      convert(arg, var_count, depth))

   return convert(term, 0)


# import inspect

# def get_stack_depth():
#     return len(inspect.stack())

def debruijn_generator():
    global MAX_DEPTH
    def term_gen(scope_depth, depth):
        if scope_depth:
            choices = ['var', 'abs', 'app'] if depth > 0 else ['var']
        else:
            choices = ['abs', 'abs', 'app']

        match random.choice(choices):
            case 'var':
                # Pick a random index from 0 to scope_depth-1
                return ('var', random.randrange(scope_depth))
            case 'abs':
                body = term_gen(scope_depth + 1, depth - 1)
                return ('abs', body)
            case 'app':
                func = term_gen(scope_depth, depth - 1)
                arg = term_gen(scope_depth, depth - 1)
                return ('app', func, arg)

    return debruijn_to_names(term_gen(0, MAX_DEPTH))




# PROBABILITY - Tuple reresentation with MACROS (used as combinators)


def probability(expr):
    fresh_var_gen = make_fresh_var_gen()

    def term_gen(expr, scope, depth):

        if scope:
            choices = ['var', 'abs', 'app'] if depth > 0 else ['var']
        else:
            choices = ['abs', 'abs', 'app']

        if MACROS_ENABLED:
            choices.append('mac')

        match expr:
            case ('var', var):
                prob_var = choices.count('var')/len(choices)
                prob_scope = 1/len(scope) if var in scope else 0
                prob = prob_var * prob_scope
                return prob
            case ('abs', var, body):
                prob_abs = choices.count('abs')/len(choices)
                prob_var = 1 if var == next(fresh_var_gen) else 0
                prob_body = term_gen(body, scope + [var], depth - 1)
                prob = prob_abs * prob_var * prob_body
                return prob
            case ('app', func, arg):
                prob_app = choices.count('app')/len(choices)
                prob_func = term_gen(func, scope, depth - 1)
                prob_arg = term_gen(arg, scope, depth - 1)
                prob = prob_app * prob_func * prob_arg
                return prob
            case str() as mac if mac in MACROS:
                prob_mac = choices.count('mac')/len(choices)
                prob_macros = 1/len(MACROS)
                prob = prob_mac * prob_macros
                return prob
            case _:
                prob = 0
                return prob

    return term_gen(expr, [], MAX_DEPTH)





### FITNESS - Tuple representation

def encode_tt(truth_table, listp=False, output_int=False):
    """Encode a truth table for a list of boolean values"""
    encoded_tt = []
    for inputs, output in truth_table:
        inputs = tuple([encode_bool(i) for i in inputs])
        if listp:
            inputs = encode_list(inputs)
        if output_int:
            encoded_tt.append((inputs, encode_int(output)))
        else:
            encoded_tt.append((inputs, encode_bool(output)))
    return encoded_tt




NOT_TRUTH_TABLE = [
    (FALSE, TRUE),
    (TRUE, FALSE),
    ]

AND_TRUTH_TABLE = [
    ((FALSE, FALSE), FALSE),
    ((FALSE, TRUE), FALSE), 
    ((TRUE, FALSE), FALSE),
    ((TRUE, TRUE), TRUE),
    ]

OR_TRUTH_TABLE = [
    ((FALSE, FALSE), FALSE),
    ((FALSE, TRUE), TRUE), 
    ((TRUE, FALSE), TRUE),
    ((TRUE, TRUE), TRUE),
    ]

XOR_TRUTH_TABLE = [
    ((FALSE, FALSE), FALSE),
    ((FALSE, TRUE), TRUE), 
    ((TRUE, FALSE), TRUE),
    ((TRUE, TRUE), FALSE),
    ]

XNOR_TRUTH_TABLE = [
    ((FALSE, FALSE), TRUE),
    ((FALSE, TRUE), FALSE), 
    ((TRUE, FALSE), FALSE),
    ((TRUE, TRUE), TRUE),
    ]


ALL_TRUTH_TABLE = encode_tt([
([], True),
([True], True),
([False], False),
([True, False], False),
([True, True], True),
([False, False, False], False),
([True, True, True], True),
([False, False, True], False),
], listp=True)

ALL_TRUTH_TABLE_TEST = encode_tt([
([], True),
([True], True),
([False], False),
([False, False], False),
((False, True), False),
([True, False], False),
([True, True], True),
([False, False, False], False),
([True, False, False], False),
([True, True, True], True),
([True, True, True, True], True),
([False, True, False, True], False),
], listp=True)

LENGTH_TRUTH_TABLE = encode_tt([
([], 0),
([True], 1),
([False, False], 2),
([False, False, False], 3),
([False, True, False], 3),
([False, False, True, False], 4),
([False, False, True, False, True], 5),
], listp=True, output_int=True)

LENGTH_TRUTH_TABLE_TEST = encode_tt([
([], 0),
([True], 1),
([False], 1),
([False, False], 2),
([False, True], 2),
([False, False, False], 3),
([False, True, False], 3),
([True, True, True], 3),
([False, False, True, False], 4),
([False, False, True, False, True], 5),
([False, False, False, True, False, True], 6),
([False, False, False, True, False, True, False], 7),
([True, False, True, False, False, True, False, True], 8),
([False, True, False, True, False, False, True, False, True], 9),
], listp=True, output_int=True)

# this also works
# LENGTH_TRUTH_TABLE_TEST = [
#     (encode_list([]), ZERO),
#     (encode_list([TRUE]), ONE),
#     (encode_list([FALSE, TRUE]), TWO),
#     (encode_list([FALSE, FALSE, FALSE, FALSE, FALSE, FALSE]), SIX)
# ]

LAST_TRUTH_TABLE = encode_tt([
([True], True),
([False], False),
([False, False], False),
([False, True], True),
([True, True], True),
([False, False, False], False),
([True, False, True], True),
([True, True, False], False),
([True], True),
([True, True], True),
([False, False, False], False),
([True, False, True], True),
([True, True, True], True),
([False, False, True], True),
], listp=True)


def encode_integer_table(table):
    return [((encode_int(a), encode_int(b)), encode_int(c)) for (a, b), c in table]

PLUS_TRAINING_CASES = encode_integer_table([
    ((1, 0), 1),
    ((1, 1), 2),
    ((2, 0), 2),
    ((0, 3), 3),
    ((2, 1), 3),
    ((2, 3), 5),
    ((0, 6), 6),
    ((1, 7), 8),
])

PLUS_TEST_CASES = encode_integer_table([
    ((0, 0), 0),
    ((0, 1), 1),
    ((1, 0), 1),
    ((1, 1), 2),
    ((0, 2), 2),
    ((2, 0), 2),
    ((0, 3), 3),
    ((2, 1), 3),
    ((2, 3), 5),
    ((4, 1), 5),
    ((4, 2), 6),
    ((1, 5), 6),
    ((0, 6), 6),
    ((1, 7), 8),
    ((7, 2), 9),
    ((5, 4), 9)
])

SUCC_TRAINING_CASES = [
    (ZERO, ONE),
    (ONE, TWO),
    (THREE, FOUR)
]

SUCC_TEST_CASES = [
    (ZERO, ONE),
    (ONE, TWO),
    (TWO, THREE),
    (THREE, FOUR),
]

IS_ZERO_TRAINING_CASES = [
    (ZERO, TRUE),
    (ONE, FALSE),
    (THREE, FALSE),
]

IS_ZERO_TEST_CASES = [
    (ZERO, TRUE),
    (ONE, FALSE),
    (TWO, FALSE),
    (THREE, FALSE),
    (FOUR, FALSE),
    (FIVE, FALSE),
    (SIX, FALSE),
    (SEVEN, FALSE),
    (EIGHT, FALSE),
    (NINE, FALSE)
]

FOLD_TRAINING_CASES = [
    # fzl, r
    ((AND, TRUE, encode_list([TRUE])), TRUE),
    ((AND, TRUE, encode_list([TRUE, FALSE])), FALSE),
    ((OR, FALSE, encode_list([FALSE])), FALSE),
    ((OR, FALSE, encode_list([TRUE, FALSE])), TRUE),
    ((XOR, FALSE, encode_list([TRUE, TRUE])), FALSE),
    ((XNOR, TRUE, encode_list([FALSE, FALSE, FALSE])), FALSE),
]

FOLD_TEST_CASES = [
    # fzl, r
    ((AND, TRUE, encode_list([TRUE])), TRUE),
    ((AND, TRUE, encode_list([TRUE, FALSE])), FALSE),
    ((AND, TRUE, encode_list([TRUE, TRUE])), TRUE),
    ((OR, FALSE, encode_list([FALSE])), FALSE),
    ((OR, FALSE, encode_list([TRUE, FALSE])), TRUE),

    ((XOR, FALSE, encode_list([FALSE])), FALSE),
    ((XOR, FALSE, encode_list([TRUE])), TRUE),
    ((XOR, FALSE, encode_list([TRUE, FALSE])), TRUE),
    ((XOR, FALSE, encode_list([FALSE, FALSE, TRUE])), TRUE),

    ((XNOR, TRUE, encode_list([FALSE])), FALSE),
    ((XNOR, TRUE, encode_list([TRUE])), TRUE),
    ((XNOR, TRUE, encode_list([TRUE, FALSE])), FALSE),
    ((XNOR, TRUE, encode_list([TRUE, TRUE])), TRUE),
    ((XNOR, TRUE, encode_list([FALSE, FALSE, FALSE])), FALSE),    
]



truth_tables = {
    'NOT': NOT_TRUTH_TABLE,
    'AND': AND_TRUTH_TABLE,
    'OR': OR_TRUTH_TABLE,
    'XOR': XOR_TRUTH_TABLE,
    'XNOR': XNOR_TRUTH_TABLE,
    'ALL': ALL_TRUTH_TABLE,
    'ALL_TEST': ALL_TRUTH_TABLE_TEST,
    'LAST': LAST_TRUTH_TABLE,
    'FOLD': FOLD_TRAINING_CASES,
    'FOLD_TEST': FOLD_TEST_CASES,
    'LENGTH': LENGTH_TRUTH_TABLE,
    'LENGTH_TEST': LENGTH_TRUTH_TABLE_TEST,
    'PLUS': PLUS_TRAINING_CASES,
    'PLUS_TEST': PLUS_TEST_CASES,
    'IS_ZERO': IS_ZERO_TRAINING_CASES,
    'IS_ZERO_TEST': IS_ZERO_TEST_CASES
}



def apply_unary(f, arg):
    return safe_apply(f, arg)
    
def apply_binop(f, args):
    assert len(args) == 2, "apply_binop requires f and then args of length 2"
    return safe_apply(safe_apply(f, args[0]), args[1])

def apply_trinop(f, args):
    assert len(args) == 3, "apply_trinop requires f and then args of length 3"
    return safe_apply(safe_apply(safe_apply(f, args[0]), args[1]), args[2])

def unary_fitness(expr, truth_table, metric=shd):
    """Fitness function for unary operations (eg NOT)"""
    try:
        # Sum the distances between expected and actual outputs for each input 
        return mean(metric(apply_unary(expr, a), b) for a, b in truth_table)
    except ValueError: # eg if some application gives None
        return 1

def binop_fitness(expr, truth_table, metric=shd):
    """Fitness function for boolean operations (eg AND)"""
    try:
        # Sum the distances between expected and actual outputs for each input pair
        return mean(metric(apply_binop(expr, ab), c) for ab, c in truth_table)
    except ValueError:
        return 1

def list_fitness(expr, truth_table, metric=shd):
    #global fitness_call_count, fitness_exception_count
    #fitness_call_count += 1
    # print(expr)
    # for a, b in truth_table:
    #     print('---')
    #     print(a)
    #     print(b)
    #     print(safe_apply(expr, a))
    # print()
    try:
        return mean(metric(safe_apply(expr, a), b) for a, b in truth_table) 
    except Exception as e:
        # print(f"ValueError in list_fitness: {e}")
        # print(f"expr: {expr}")
        # fitness_exception_count += 1
        # if fitness_call_count % 100 == 0:  # Print every 100 calls
        #     print(f"Fitness exceptions: {fitness_exception_count}/{fitness_call_count} = {fitness_exception_count/fitness_call_count*100:.1f}%")
        return 1

def fold_fitness(expr, truth_table, metric=shd): # FOLD f z l
    try:
        return mean(metric(apply_trinop(expr, fzl), r) for fzl, r in truth_table) 
    except ValueError:
        return 1

def not_fitness(expr, metric=shd):
    try:
        truth_table = truth_tables['NOT']
        return mean(metric(apply_unary(expr, a), b) for a, b in truth_table)
    except ValueError:
        return 1

def all_fitness(expr, metric=shd):
    return list_fitness(expr, truth_tables['ALL'], metric=metric)


def generic_fitness(expr, fitcases, apply, metric=shd, timeout_seconds=1):

    # Set up a timeout to stop long-running evaluations
    old_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout_seconds) 

    try:
        result = mean(metric(apply(expr, a), b) for a, b in fitcases)
    except ValueError:
        result = 1
    except TimeoutException:
        result = 1  # Treat timeout as invalid program
    finally:
        # Always clean up the alarm
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)
    return result
