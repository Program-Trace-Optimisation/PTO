import sys

from lc_functions import *

from itertools import count

import signal

class TimeoutException(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutException("Function call timed out")




MAX_DEPTH = 10
MACROS_ENABLED = True
MACROS = ['NOT', 'AND', 'OR', 'TRUE', 'FALSE'] # , 'FOLD', 'SUCC', 'ZERO'

make_fresh_var_gen = lambda : (f"x{i}" for i in count(1))

def alpha_convert(term, base='x'):
    """
    Alpha-converts a Lambda Calculus term to a canonical form.
    This involves renaming bound variables to a standard set of names
    (e.g., x1, x2, x3, ...).
    """
    env = {}
    next_var_index = 1

    def convert(term, current_env):
        nonlocal next_var_index
        match term:
            case ('var', name):
                return ('var', current_env.get(name, name))
            case ('abs', var_name, body):
                new_var_name = f'{base}{next_var_index}'
                next_var_index += 1
                new_env = {**current_env, var_name: new_var_name}
                return ('abs', new_var_name, convert(body, new_env))
            case ('app', func, arg):
                return ('app', convert(func, current_env), convert(arg, current_env))
            case None:
                raise ValueError(f'None in alpha_convert')

            case _:
                return term

    return convert(term, env)



# Create macro environment from global variables
# macro_env = {name: globals()[name] for name in MACROS}


def normalize_lambda_expression(expr, macros=None):
    """
    Normalize a lambda expression in tuple form by renaming variables consistently.
    Handles variable shadowing and supports macros.
    
    Args:
        expr: Lambda expression in tuple form ('var', 'abs', or 'app')
        macros: Set of strings representing macros (default: None)
    
    Returns:
        Normalized lambda expression
    """
    if macros is None:
        macros = set(MACROS) if MACROS_ENABLED else set()
    # print('in norm, macros =', macros)
    
    # Generate fresh variables
    fresh_var_gen = make_fresh_var_gen()
    
    # Map from original variable names to new names
    var_map = {}
    
    def normalize(expr, scope):
        # If expression is a macro, return it as is
        if isinstance(expr, str) and expr in macros:
            return expr
        
        match expr:
            case ('var', name):
                # Look up variable in current scope
                if name in scope:
                    return ('var', scope[name])
                else:
                    # This should not happen with well-formed expressions,
                    # but handle it gracefully by creating a new variable
                    new_name = next(fresh_var_gen)
                    return ('var', new_name)
                
            case ('abs', param, body):
                # Create a new variable name for the parameter
                new_param = next(fresh_var_gen)
                
                # Create new scope with the parameter mapped to its new name
                new_scope = scope.copy()
                new_scope[param] = new_param
                
                # Normalize the body with the updated scope
                new_body = normalize(body, new_scope)
                
                return ('abs', new_param, new_body)
                
            case ('app', func, arg):
                # Normalize both parts independently with the same scope
                new_func = normalize(func, scope)
                new_arg = normalize(arg, scope)
                
                return ('app', new_func, new_arg)
            
            case None:
                raise ValueError(f'None in normalize_lambda_expression')

                
            # Handle any other form (including macros not in the provided set)
            case _:
                return expr
    
    # Start normalization with empty scope
    return normalize(expr, {})

# Example usage
def print_lambda_expr(expr, indent=0):
    """Pretty print a lambda expression for debugging"""
    if isinstance(expr, str):
        return expr
    
    match expr:
        case ('var', name):
            return name
        case ('abs', param, body):
            return f"(λ{param}.{print_lambda_expr(body)})"
        case ('app', func, arg):
            return f"({print_lambda_expr(func)} {print_lambda_expr(arg)})"
        case None:
            raise ValueError(f'None in print_lambda_expr')
        case _:
            return str(expr)




def expand_macros_new(term):

    next_var_index = 1
        
    def expand_helper(term):
        nonlocal next_var_index
        match term:
            case ('var', name):
                return term
            case ('abs', param, body):
                return ('abs', param, expand_helper(body))
            case ('app', func, arg):
                # Keep expanding func until it's no longer a macro name
                while isinstance(func, str) and func in macro_env:
                    func = macro_env[func]
                func = normalize_lambda_expression(func, base=f'_expand{next_var_index}')
                next_var_index += 1
                expanded_func = expand_helper(func)
                expanded_arg = expand_helper(arg)
                return ('app', expanded_func, expanded_arg)
            case str() if term in macro_env:
                # Keep expanding until it's not a macro name
                result = term
                while isinstance(result, str) and result in macro_env:
                    result = macro_env[result]
                result = normalize_lambda_expression(result, base=f'_expand{next_var_index}')
                next_var_index += 1
                return expand_helper(result)
            case None:
                raise ValueError(f'None in expand_helper')
            case _:
                return term

    return normalize_lambda_expression(expand_helper(term), base=f'x')


def expand_macros(term):
        
    match term:
        case ('var', name):
            return term
        case ('abs', param, body):
            return ('abs', param, expand_macros(body))
        case ('app', func, arg):
            # Keep expanding func until it's no longer a macro name
            if func is None: raise ValueError(f'None before macro_env')
            while isinstance(func, str) and func in macro_env:
                func = macro_env[func]
            if func is None: raise ValueError(f'None after macro_env')
            expanded_func = expand_macros(func)
            if expanded_func is None: raise ValueError(f'expanded_func None after expand_macros')
            expanded_arg = expand_macros(arg)
            if expanded_func is None: raise ValueError(f'expanded_arg None after expand_macros')
            return ('app', expanded_func, expanded_arg)
        case str() if term in macro_env:
            # Keep expanding until it's not a macro name
            result = term
            while isinstance(result, str) and result in macro_env:
                result = macro_env[result]
            result = expand_macros(result)
            if result is None: raise ValueError(f'result None after expand_macros')
            return result
        case None:
            raise ValueError(f'None in expand_macros')
        case _:
            return term



# the discrete metric on lambda expressions. they are equal 
# if and only if the tuple representations, after normalisation, are exactly equal.
def lambda_equivalent(t1, t2, rename=True):

    if t1 is None or t2 is None:
        raise ValueError(f'None in lambda_equivalent')

    # not sure if this preliminary check saves time in practice, but this '==' can shortcut
    # so maybe.
    if t1 == t2: return True 

    if rename:
        # t1 = alpha_convert(t1, base='y')
        # t2 = alpha_convert(t2, base='y')
        t1 = normalize_lambda_expression(t1)
        t2 = normalize_lambda_expression(t2)
    return t1 == t2

def discrete_metric(t1, t2, rename=True):
    return not lambda_equivalent(t1, t2, rename=rename)

# Distance between lambda expressions - Structural Hamming Distance - Tuple representation
def shd(t1, t2, rename=True):

    if t1 is None:
        raise ValueError(f't1 is None in shd')
    if t2 is None:
        raise ValueError(f't2 is None in shd')
    
    if rename:
        # t1 = alpha_convert(t1, base='y')
        # t2 = alpha_convert(t2, base='y')
        t1 = normalize_lambda_expression(t1)
        t2 = normalize_lambda_expression(t2)

    # print(t1)
    # print(t2)

    def helper(t1, t2):
        # Different constructors (abs/app/var) - incomparable
        if t1[0] != t2[0]:
            return 1.0

        # Both variables
        if t1[0] == 'var':
            # Compare constructor (var,var) and variable names
            return (0.0 + (1.0 if t1[1] != t2[1] else 0.0)) / 2

        # Both abstractions
        if t1[0] == 'abs':
            # Compare constructor (abs,abs), parameter names, and bodies
            param_dist = 1.0 if t1[1] != t2[1] else 0.0
            body_dist = helper(t1[2], t2[2])
            return (0.0 + param_dist + body_dist) / 3

        # Both applications
        if t1[0] == 'app':
            # Compare constructor (app,app), functions and arguments
            func_dist = helper(t1[1], t2[1])
            arg_dist = helper(t1[2], t2[2])
            return (0.0 + func_dist + arg_dist) / 3
        
    return helper(t1, t2)


# Evaluator of lambda expressions - Tuple representation

def substitute(term, var_name, replacement):
    """Substitute var_name with replacement in term"""
    match term:
        case ('var', name):
            return replacement if name == var_name else term
        case ('abs', param, body):
            # Don't substitute if parameter shadows the variable
            if param == var_name:
                return term
            return ('abs', param, substitute(body, var_name, replacement))
        case ('app', func, arg):
            return ('app',
                   substitute(func, var_name, replacement),
                   substitute(arg, var_name, replacement))

            
def evaluate(term):
    """Beta reduce a lambda term to normal form"""
    # First expand any macros
    term = expand_macros(term)
    
    match term:
        case ('var', _):
            return term
        case ('abs', param, body):
            #return term
            
            # alternative proposed by Claude for "complete evaluation", makes some
            # tests pass and others fail:
            # Evaluate the body inside an abstraction
            new_body = evaluate(body)
            return ('abs', param, new_body)
        case ('app', func, arg):
            # Evaluate function and argument first
            #print('evaluate app')
            #print(f'func {func}')
            #print(f'arg {arg}')
            if func is None:
                raise ValueError(f"None in func in app")
            func = evaluate(func)
            if func is None:
                raise ValueError(f"None in func from evaluate")
            arg = evaluate(arg)

            # If function is an abstraction, perform beta reduction
            if func[0] == 'abs':
                param, body = func[1], func[2]
                # Substitute parameter with argument in body and evaluate
                result = evaluate(substitute(body, param, arg))
                if result is None:
                    raise ValueError(f"None in result from evaluate recursive call")
                return result
            else:
                return ('app', func, arg)
        case None:
            raise ValueError(f"None in evaluate")
        case _:
            raise ValueError(f"Unexpected input in evaluate(): {term}")


evaluate_orig = evaluate
def evaluate(term): #, macro_env=macro_env):
  return evaluate_orig(expand_macros(term)) #, macro_env))





# ----- Encoding/Decoding Utilities -----

def encode_bool(b):
    """Encode a Python boolean to a Lambda Calculus boolean."""
    return TRUE if b else FALSE

def decode_bool(lc_bool):
    """Decode a Lambda Calculus boolean to a Python boolean."""
    return lc_bool == TRUE

def encode_int(n):
    """Convert a Python integer to Church numeral"""
    d = {
        0: ZERO,
        1: ONE,
        2: TWO,
        3: THREE,
        4: FOUR,
        5: FIVE,
        6: SIX,
        7: SEVEN,
        8: EIGHT,
        9: NINE,
    }
    return d[n]

def encode_list(python_list):
    """Convert a Python list of lambda expressions into Church-encoded list"""

    result = 'NIL'  # Start with empty list
    # Add elements from right to left using CONS
    for x in reversed(python_list):
        assert x not in (True, False) # NB, we assume the elements are encoded already
        result = ('app', ('app', 'CONS', x), result)
    return result



def safe_apply(f, arg):
    """Apply term to arg with recursion limit"""

    # print(f'in safe_apply f {f} arg {arg}')
    if f is None:
        raise ValueError(f'in safe_apply f is None')

    sys.setrecursionlimit(60) # chosen as the lowest value for which all tests pass 

    try:
        # original where we rename both f and arg independently first: tests pass
        # result = evaluate(('app', alpha_convert(f, base='x'), alpha_convert(arg, base='y')))

        # new version where the normalise function fixes everything: tests pass
        # result = normalize_lambda_expression(evaluate(normalize_lambda_expression(('app', f, arg)))) 

        # the extra outer norm above is debatable. it does normalise the result. but sometimes
        # our lambda_equivalent and shd functions will be comparing against expressions that
        # don't come from safe_apply, so they need to normalise internally anyway. so there
        # is a slight waste of time here. (possibly there is a slight benefit to 
        # having normalised outputs from safe_apply anyway.) so here is a version without 
        # the outer norm. tests pass.
        result = evaluate(normalize_lambda_expression(('app', f, arg)))
        # print('in safe_apply, no recursion error')
    except RecursionError: # do not silently catch other errors, as we want to know about them
        # print(f"RecursionError with f \n{f} \n and arg \n {arg}")
        # sys.exit()
        result = None
    except TimeoutException:
        result = None  # Treat timeout as invalid program

    sys.setrecursionlimit(1000) # back to the original

    return result

# apply = safe_apply






if __name__ == "__main__":
    # test expand_macros:
    xs = (
        'FOLD',
    )
    for x in xs:
        print(x)
        print(expand_macros(x))
        print(normalize_lambda_expression(expand_macros(x)))


# Test the normalizer
if __name__ == "__main__":
    # Example with shadowing: (λx.(λx.x) (x y))
    test_expr = ('abs', 'x', ('app', ('abs', 'x', ('var', 'x')), ('app', ('var', 'x'), ('var', 'y'))))
    
    print("Original:", print_lambda_expr(test_expr))
    normalized = normalize_lambda_expression(test_expr)
    print("Normalized:", print_lambda_expr(normalized))
    
    # Test with macros
    test_with_macro = ('app', 'FOLD', ('abs', 'x', ('var', 'x')))
    normalized_with_macro = normalize_lambda_expression(test_with_macro, base='y', macros={'FOLD'})
    print("With macro:", print_lambda_expr(normalized_with_macro))