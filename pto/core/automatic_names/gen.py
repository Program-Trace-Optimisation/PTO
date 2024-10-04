
import ast
import inspect
import functools

from .annotators import func_name, iter_name, Loop_name
from .autogens import rnd
from .autoplay import tracer
from .ast_trans import transform_ast, ast_transformers

#---

# AST transormer decorators factory
def ast_transform_decorator(transformations, environment=None, at_syntax=True):
    def decorator(func):
        # Get the source code of the function
        source = inspect.getsource(func)

        # Skip decorator line if used as @decorator
        if at_syntax: 
            source = '\n'.join(source.splitlines()[1:]) 

        #print(source)
        
        # Parse the source code into an AST
        tree = ast.parse(source)
        
        # Apply transformations
        for t in transformations:
            tree = t.visit(tree)
        tree = ast.fix_missing_locations(tree)

        #print(ast.unparse(tree))
        
        # Compile the modified AST
        compiled_code = compile(tree, '<string>', 'exec')
        
        # Use the original function's environment and the specified environment
        env = func.__globals__ | (environment or {})

        # execute transformed function definition which overrides previous definition
        exec(compile(tree, '<ast>', 'exec'), env)
    
        # reference to transformed function
        new_func = env[func.__name__]        
                
        # Copy the original function's metadata
        functools.update_wrapper(new_func, func)

        # Store source code
        new_func._old_source = source
        new_func._new_source = ast.unparse(tree)
        
        return new_func
    return decorator

#---

transformations = ast_transformers
environment = {'func_name' : func_name, 'iter_name' : iter_name, 'Loop_name' : Loop_name, 'rnd' : rnd}

gen_fun = ast_transform_decorator(transformations, environment, at_syntax = False)
gen = ast_transform_decorator(transformations, environment)

#---

def play_gen(generator):
    generator = gen_fun(generator)
    return tracer.play(generator)

