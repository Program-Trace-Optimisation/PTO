from lc import *
from lc_functions import *
from lc_pto import *
import lc, lc_pto

def test(x):
    if isinstance(x, str):
        print('\ntest ' + x, end=' ')
    else:
        if x:
            print('😊', end='')
        else:
            print('❌', end='')



print("macros")
print(MACROS)
MACROS_ENABLED, lc.MACROS_ENABLED, lc_pto.MACROS_ENABLED = False, False, False
MACROS_ENABLED, lc.MACROS_ENABLED, lc_pto.MACROS_ENABLED = True, True, True
print("MACROS_ENABLED")
print(MACROS_ENABLED, lc.MACROS_ENABLED, lc_pto.MACROS_ENABLED)


test('safe_apply')
test(lambda_equivalent(FALSE, safe_apply(NOT, TRUE)))


test('NOT, AND, OR, XOR, XNOR')
test(lambda_equivalent(safe_apply(NOT, TRUE), FALSE))
test(lambda_equivalent(safe_apply(NOT, FALSE), TRUE))
test(lambda_equivalent(safe_apply(safe_apply(AND, TRUE), TRUE), TRUE))
test(lambda_equivalent(safe_apply(safe_apply(AND, TRUE), FALSE), FALSE))
test(lambda_equivalent(safe_apply(safe_apply(OR, TRUE), TRUE), TRUE))
test(lambda_equivalent(safe_apply(safe_apply(OR, TRUE), FALSE), TRUE))
test(lambda_equivalent(safe_apply(safe_apply(XOR, TRUE), TRUE), FALSE))
test(lambda_equivalent(safe_apply(safe_apply(XOR, TRUE), FALSE), TRUE))
test(lambda_equivalent(safe_apply(safe_apply(XNOR, TRUE), TRUE), TRUE))
test(lambda_equivalent(safe_apply(safe_apply(XNOR, TRUE), FALSE), FALSE))



test('encode_bool, decode_bool')
test(lambda_equivalent(encode_bool(True), TRUE))
test(lambda_equivalent(encode_bool(False), FALSE))

test(encode_bool(decode_bool(TRUE)) == TRUE)
test(encode_bool(decode_bool(FALSE)) == FALSE)
test(decode_bool(encode_bool(True)) == True)
test(decode_bool(encode_bool(False)) == False)

test(lambda_equivalent(safe_apply(ALL, encode_list([])), TRUE))
test(lambda_equivalent(safe_apply(ALL, encode_list([FALSE])), FALSE))
test(lambda_equivalent(safe_apply(ALL, encode_list([TRUE, TRUE, FALSE])), FALSE))
test(lambda_equivalent(safe_apply(ALL, encode_list([TRUE, TRUE, FALSE])), FALSE))
test(lambda_equivalent(safe_apply(ALL, encode_list([TRUE, TRUE, TRUE])), TRUE))
test(lambda_equivalent(safe_apply(ALL, encode_list([FALSE, FALSE, FALSE])), FALSE))

# test('FOLD')
# test(lambda_equivalent(apply_trinop(FOLD, (AND, TRUE, encode_list([TRUE]))), TRUE))

test('shd')
test(shd(TRUE, TRUE) == 0)
test(shd(TRUE, FALSE) > 0)
test(shd(FALSE, TRUE) > 0)
test(shd(AND, OR) < shd(AND, XNOR)) # a gimmick


def test_shd():
    # Test cases
    id_fn = ('abs', 'x1', ('var', 'x1'))  # λx.x
    true = ('abs', 'x1', ('abs', 'x2', ('var', 'x1')))  # λx.λy.x
    false = ('abs', 'x1', ('abs', 'x2', ('var', 'x2')))  # λx.λy.y

    # Test variable comparison
    var1 = ('var', 'x1')
    var2 = ('var', 'x2')
    test(shd(var1, var2, rename=False) == 0.5)

    # A nuanced case: Claude says that alpha conversion does not normally
    # change the name of free variables, so the rename will not change
    # var1, var2, so the distance would remain as 0.5. however with our
    # normalize function, variables are renamed, so we should get 0.0
    test(shd(var1, var2, rename=True) == 0.0)

    TRUEx = ('abs', 'x1', ('abs', 'x2', ('var', 'x1')))
    TRUEy = ('abs', 'y1', ('abs', 'y2', ('var', 'y1')))
    test(shd(TRUEx, TRUEy, rename=False) == 0.5)
    test(shd(TRUEx, TRUEy) == 0.0)
    
    # Test abstraction comparison
    test(shd(id_fn, true) > 0)

    # Test TRUE vs FALSE
    test(shd(true, false) > 0)

    # Test incomparable terms
    var_app = ('app', ('var', 'x1'), ('var', 'x2'))  # x1 x2
    test(shd(var1, var_app) == 1.0)

test_shd()




test('abstraction renaming')
# Simple Abstraction Renaming
term1_simple = ('abs', 'x', ('var', 'x'))
term2_simple = ('abs', 'a', ('var', 'a'))
test(term1_simple != term2_simple)
test(lambda_equivalent(term1_simple, term2_simple))

# # Nested Abstractions
term1_nested = ('abs', 'x', ('abs', 'y', ('app', ('var', 'x'), ('var', 'y'))))
term2_nested = ('abs', 'a', ('abs', 'b', ('app', ('var', 'a'), ('var', 'b'))))
test(term1_nested != term2_nested)
test(lambda_equivalent(term1_nested, term2_nested))

# # Application and Abstraction
term1_app_abs = ('app', ('abs', 'x', ('var', 'x')), ('abs', 'y', ('var', 'y')))
term2_app_abs = ('app', ('abs', 'a', ('var', 'a')), ('abs', 'b', ('var', 'b')))
test(term1_app_abs != term2_app_abs)
test(lambda_equivalent(term1_app_abs, term2_app_abs))

# # Terms with Free Variables
term1_free = ('abs', 'x', ('app', ('var', 'x'), ('var', 'y'))) # 'y' is free
term2_free = ('abs', 'a', ('app', ('var', 'a'), ('var', 'y'))) # 'y' is free
test(term1_free != term2_free)
test(lambda_equivalent(term1_free, term2_free))

# # test that shadowing is handled correctly.
term1_shadow = ('abs', 'x', ('abs', 'x', ('var', 'x')))
term2_shadow = ('abs', 'a', ('abs', 'b', ('var', 'b')))
test(term1_shadow != term2_shadow)
test(lambda_equivalent(term1_shadow, term2_shadow))










test('numerals')
test(lambda_equivalent(safe_apply(IS_ZERO, ZERO), TRUE))
test(lambda_equivalent(safe_apply(IS_ZERO, ONE), FALSE))
test(lambda_equivalent(safe_apply(SUCC, ZERO), ONE))
test(lambda_equivalent(safe_apply(SUCC, ONE), TWO))
test(lambda_equivalent(safe_apply(safe_apply(PLUS, ONE), TWO), THREE))
test(lambda_equivalent(safe_apply(safe_apply(MULT, TWO), TWO), safe_apply(SUCC, THREE)))



test('pairs and projections')
# Basic pairing and extraction
test(lambda_equivalent(safe_apply(FIRST, safe_apply(safe_apply(PAIR, TRUE), FALSE)), TRUE))
test(lambda_equivalent(safe_apply(SECOND, safe_apply(safe_apply(PAIR, TRUE), FALSE)), FALSE))

# Church numerals as elements
test(lambda_equivalent(safe_apply(FIRST, safe_apply(safe_apply(PAIR, ZERO), ONE)), ZERO))
test(lambda_equivalent(safe_apply(SECOND, safe_apply(safe_apply(PAIR, ZERO), ONE)), ONE))

# Nested pairs
nested_pair = safe_apply(safe_apply(PAIR, safe_apply(safe_apply(PAIR, TRUE), FALSE)), safe_apply(safe_apply(PAIR, ZERO), ONE))
test(lambda_equivalent(safe_apply(FIRST, safe_apply(FIRST, nested_pair)), TRUE))
test(lambda_equivalent(safe_apply(SECOND, safe_apply(FIRST, nested_pair)), FALSE))
test(lambda_equivalent(safe_apply(FIRST, safe_apply(SECOND, nested_pair)), ZERO))
test(lambda_equivalent(safe_apply(SECOND, safe_apply(SECOND, nested_pair)), ONE))

# Identity property: PAIR(FIRST(p))(SECOND(p)) = p
p = safe_apply(safe_apply(PAIR, TRUE), FALSE)
reconstructed = safe_apply(safe_apply(PAIR, safe_apply(FIRST, p)), safe_apply(SECOND, p))
test(lambda_equivalent(p, reconstructed))





test('combinators')

# Test that S K I is the identity function
# S K I x = K x (I x) = x for any x
test(lambda_equivalent(safe_apply(safe_apply(S, K), I), I))


# S combinator: λx.λy.λz.x z (y z)

# Test with identity function
# S I I x = I x (I x) = x x
test_id = safe_apply(safe_apply(safe_apply(S, I), I), TRUE)
test(lambda_equivalent(test_id, safe_apply(TRUE, TRUE)))

# Test with K (constant) and I
# S K I x = K x (I x) = x
test_k_i = safe_apply(safe_apply(safe_apply(S, K), I), TRUE)
test(lambda_equivalent(test_k_i, TRUE))
test_k_i = safe_apply(safe_apply(safe_apply(S, K), I), FALSE)
test(lambda_equivalent(test_k_i, FALSE))

# Test with K K 
# S K K x = K x (K x) = x
test_k_k = safe_apply(safe_apply(safe_apply(S, K), K), TRUE)
test(lambda_equivalent(test_k_k, TRUE))
test_k_k = safe_apply(safe_apply(safe_apply(S, K), K), FALSE)
test(lambda_equivalent(test_k_k, FALSE))

# Test boolean logic: S K K is equivalent to I
test(lambda_equivalent(safe_apply(safe_apply(S, K), K), I))

# Test with TRUE and FALSE
# S TRUE FALSE ONE = TRUE ONE (FALSE ONE)
# TRUE ONE = λb.ONE
# FALSE ONE = I
# So (λb.ONE) I = ONE
test_tf = safe_apply(safe_apply(safe_apply(S, TRUE), FALSE), ONE)
test(lambda_equivalent(test_tf, ONE))

# A better test: S K S x = K x (S x) = x
test_k_s = safe_apply(safe_apply(safe_apply(S, K), S), FALSE)
test(lambda_equivalent(test_k_s, FALSE))
test_k_s = safe_apply(safe_apply(safe_apply(S, K), S), TRUE)
test(lambda_equivalent(test_k_s, TRUE))

# S (K K) I x = K x (I x) = K x x = λy.x
# For ZERO: K ZERO (I ZERO) = λy.ZERO
test_kk_i = safe_apply(safe_apply(safe_apply(S, safe_apply(K, K)), I), ZERO)
test(lambda_equivalent(test_kk_i, safe_apply(K, ZERO)))

# Test that S combinator distributes arguments correctly
# S K K x = K x (K x) = x
test_dist = safe_apply(safe_apply(safe_apply(S, K), K), TRUE)
test(lambda_equivalent(test_dist, TRUE))

# Tests for Lambda Calculus List Functions - removing for now, unsure if LIST makes sense
# # Test LIST construction
# test(lambda_equivalent(LIST, ('app', ('app', CONS, TRUE), TRUE)))

# # Test PREPEND function
# test(lambda_equivalent(
#     safe_apply(safe_apply(PREPEND, LIST), ONE),
#     safe_apply(safe_apply(CONS, FALSE), safe_apply(safe_apply(CONS, ONE), LIST))
# ))



test(lambda_equivalent(safe_apply(safe_apply(safe_apply(S, K), I), TRUE), TRUE))
test(lambda_equivalent(safe_apply(safe_apply(safe_apply(S, K), I), FALSE), FALSE))




test('bool fitness')
test(unary_fitness(NOT, truth_tables['NOT']) == 0)
test(generic_fitness(NOT, truth_tables['NOT'], apply_unary) == 0)
test(binop_fitness(AND, truth_tables['AND']) == 0)
test(generic_fitness(AND, truth_tables['AND'], apply_binop) == 0)
test(binop_fitness(OR, truth_tables['AND']) > 0)
test(generic_fitness(OR, truth_tables['AND'], apply_binop) > 0)
test(binop_fitness(OR, truth_tables['OR']) == 0)
test(generic_fitness(OR, truth_tables['OR'], apply_binop) == 0)
test(binop_fitness(XOR, truth_tables['XOR']) == 0)
test(generic_fitness(OR, truth_tables['OR'], apply_binop) == 0)
test(binop_fitness(XNOR, truth_tables['XNOR']) == 0)
test(generic_fitness(XNOR, truth_tables['XNOR'], apply_binop) == 0)
test(binop_fitness(XNOR, truth_tables['XOR']) > 0)
test(generic_fitness(XNOR, truth_tables['XOR'], apply_binop) > 0)


test('numerals fitness')
test(binop_fitness(PLUS, PLUS_TRAINING_CASES) == 0)
test(generic_fitness(PLUS, PLUS_TRAINING_CASES, apply_binop) == 0)
test(binop_fitness(PLUS, PLUS_TEST_CASES) == 0)
test(generic_fitness(PLUS, PLUS_TEST_CASES, apply_binop) == 0)
test(unary_fitness(SUCC, SUCC_TRAINING_CASES) == 0)
test(generic_fitness(SUCC, SUCC_TRAINING_CASES, apply_unary) == 0)
test(unary_fitness(SUCC, SUCC_TEST_CASES) == 0)
test(generic_fitness(SUCC, SUCC_TEST_CASES, apply_unary) == 0)

test(unary_fitness(IS_ZERO, IS_ZERO_TRAINING_CASES) == 0)
test(generic_fitness(IS_ZERO, IS_ZERO_TRAINING_CASES, apply_unary) == 0)
test(unary_fitness(IS_ZERO, IS_ZERO_TEST_CASES) == 0)
test(generic_fitness(IS_ZERO, IS_ZERO_TEST_CASES, apply_unary) == 0)

test('list fitness')
test(list_fitness(ALL, truth_tables['ALL']) == 0)
test(generic_fitness(ALL, truth_tables['ALL'], apply_unary) == 0)
test(list_fitness(ALL, truth_tables['ALL_TEST']) == 0)
test(generic_fitness(ALL, truth_tables['ALL_TEST'], apply_unary) == 0)
test(fold_fitness(FOLD, truth_tables['FOLD']) == 0)
test(generic_fitness(FOLD, truth_tables['FOLD'], apply_trinop) == 0)
test(fold_fitness(FOLD, truth_tables['FOLD_TEST']) == 0)
test(generic_fitness(FOLD, truth_tables['FOLD_TEST'], apply_trinop) == 0)
test(list_fitness(LENGTH, truth_tables['LENGTH']) == 0)
test(generic_fitness(LENGTH, truth_tables['LENGTH'], apply_unary) == 0)
test(list_fitness(LENGTH, truth_tables['LENGTH_TEST']) == 0)
test(generic_fitness(LENGTH, truth_tables['LENGTH_TEST'], apply_unary) == 0)


test('generators\n')
print()
for name, tt, apply in (
    ('NOT', truth_tables['NOT'], apply_unary),
    ('AND', truth_tables['AND'], apply_binop),
    ('PLUS', PLUS_TRAINING_CASES, apply_binop),
    ('SUCC', SUCC_TRAINING_CASES, apply_unary),
    ('IS_ZERO', IS_ZERO_TRAINING_CASES, apply_unary),
    ('ALL', truth_tables['ALL'], apply_unary),
    ('FOLD', truth_tables['FOLD_TEST'], apply_trinop),
    ('LENGTH', truth_tables['LENGTH_TEST'], apply_unary),
):
    for generator in (tuple_generator, debruijn_generator):
        print(f"fitness random program ({generator.__name__:20} rep) on {name:10}: {generic_fitness(generator(), tt, apply):.2f}")

# print()
# for a, b in truth_tables['LENGTH_TEST']:
#     print(a)
#     print(b)
#     print()


test('generator (MACROS_ENABLED TRUE)\n')
lc_pto.MACROS_ENABLED = lc.MACROS_ENABLED = MACROS_ENABLED = True
for i in range(5):
    term = tuple_generator()
    print(term)

test('generator (MACROS_ENABLED FALSE)\n')
lc_pto.MACROS_ENABLED = lc.MACROS_ENABLED = MACROS_ENABLED = False
for i in range(5):
    term = tuple_generator()
    print(term)

test('de bruijn generator')
for i in range(5):
    term = debruijn_generator()
    print(term)
    


# recursion error
# test(list_fitness(LAST, LAST_TRUTH_TABLE) == 0)


# test(unary_fitness(FACTORIAL, truth_tables['FACT']) == 0)



# for ab, c in truth_tables['AND']:
#     print(ab, c)
#     result = safe_apply(safe_apply(AND, ab[0]), ab[1])
#     print(result)
#     print(shd(result, c))
#     print(shd(result, expand_macros(c)))
#     #print(binop_fitness(AND, truth_tables['AND']))
#     print('')






print()