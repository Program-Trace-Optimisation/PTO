from ..rewrite import rewrite_function
from .annotators import func_name, iter_name, Loop_name
from .autogens import rnd
from .autoplay import tracer
from .ast_trans import transform_ast, ast_transformers

# ---


def ast_transform_decorator(transformations, environment=None, at_syntax=True):
    """
    Create a decorator that applies AST transformations to functions.

    Takes a list of AST transformers and an optional environment dictionary,
    returns a decorator that applies these transformations to functions.
    The transformed function is executed in an environment that combines
    the original function's globals (and enclosing variables, for a nested
    function) with the provided environment dict.

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
        # Skip the decorator line if used as @decorator
        new_func, source, new_source = rewrite_function(
            func, transformations, environment, skip_first_line=at_syntax
        )

        # Store source code
        new_func._old_source = source
        new_func._new_source = new_source

        return new_func

    return decorator


# ---

# Create environment with necessary functions
transformations = ast_transformers
environment = {
    "func_name": func_name,
    "iter_name": iter_name,
    "Loop_name": Loop_name,
    "rnd": rnd,
}

# Create decorator variants
gen_fun = ast_transform_decorator(transformations, environment, at_syntax=False)
gen = ast_transform_decorator(transformations, environment)

# ---


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
