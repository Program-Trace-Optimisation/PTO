
import ast
import inspect
import functools

from .annotators import func_name, iter_name, Loop_name
from .autogens import rnd
from .autoplay import tracer
from .ast_trans import transform_ast, ast_transformers

#---

def ast_transform_decorator(transformations, environment=None, at_syntax=True):
   """
   Create a decorator that applies AST transformations to functions.
   
   Takes a list of AST transformers and an optional environment dictionary,
   returns a decorator that applies these transformations to functions.
   The transformed function is executed in an environment that combines
   the original function's globals with the provided environment dict.
   
   Args:
       transformations: List of AST transformer objects to apply
       environment: Optional dict of names to make available to transformed code
       at_syntax: Whether decorator is used with @ syntax
       
   Returns:
       Decorator function that applies the transformations
       
   Example:
       @gen  # Using @ syntax (at_syntax=True)
       def my_generator():
           for i in range(10):
               return rnd.uniform(0, 1)
               
       # Without @ syntax (at_syntax=False)
       def other_generator():
           return [rnd.choice([1,2,3]) for _ in range(5)]
       other_generator = gen_fun(other_generator)
   """
   def decorator(func):
       # Get the source code of the function
       source = inspect.getsource(func)

       # Skip decorator line if used as @decorator
       if at_syntax: 
           source = '\n'.join(source.splitlines()[1:]) 
       
       # Parse the source code into an AST
       tree = ast.parse(source)
       
       # Apply transformations
       for t in transformations:
           tree = t.visit(tree)
       tree = ast.fix_missing_locations(tree)
       
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

# Create environment with necessary functions
transformations = ast_transformers
environment = {'func_name': func_name, 
             'iter_name': iter_name, 
             'Loop_name': Loop_name, 
             'rnd': rnd}

# Create decorator variants
gen_fun = ast_transform_decorator(transformations, environment, at_syntax=False)
gen = ast_transform_decorator(transformations, environment)

#---

def play_gen(generator):
   """
   Transform and play a generator function with tracer.
   
   Applies AST transformations to the generator function and then
   executes it with the tracer to record its operation.
   
   Args:
       generator: Generator function to transform and play
       
   Returns:
       Tuple of (solution, trace) from tracer.play
       
   Example:
       def my_generator():
           return from [rnd.uniform(0,1) for _ in range(5)]
           
       solution, trace = play_gen(my_generator)
   """
   generator = gen_fun(generator)
   return tracer.play(generator)