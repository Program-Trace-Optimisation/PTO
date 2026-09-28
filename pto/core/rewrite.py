"""Rewrite a function's source with AST transformers.

Shared by the two implementations of structured names: automatic_names
(annotates the generator so names are built at run time) and compiled_names
(injects the names at compile time).
"""

import ast
import functools
import inspect
import textwrap


def closure_vars(func):
    """Variables a nested function uses from its enclosing functions, by name."""
    out = {}
    for name, cell in zip(func.__code__.co_freevars, func.__closure__ or ()):
        try:
            out[name] = cell.cell_contents
        except ValueError:  # enclosing variable not assigned yet
            pass
    return out


def rewrite_function(func, transformers, environment=None, skip_first_line=False):
    """
    Re-parse func's source, apply transformers, and define the result again.

    The new function runs with func's globals, the variables it uses from
    enclosing functions (so func can be nested), and `environment`, which
    takes precedence.

    Args:
        func: a function defined with def in a file or notebook cell
        transformers: ast.NodeTransformer instances, applied in order
        environment: optional dict of extra names for the new function
        skip_first_line: drop the first source line (a decorator line)

    Returns:
        (new_func, source, new_source): the new function, with func's
        metadata, and its source before and after the transformation
    """
    source = inspect.getsource(func)
    if skip_first_line:
        source = "\n".join(source.splitlines()[1:])
    source = textwrap.dedent(source)

    tree = ast.parse(source)
    for t in transformers:
        tree = t.visit(tree)
    tree = ast.fix_missing_locations(tree)

    env = func.__globals__ | closure_vars(func) | (environment or {})
    exec(compile(tree, "<ast>", "exec"), env)

    new_func = env[func.__name__]
    functools.update_wrapper(new_func, func)
    return new_func, source, ast.unparse(tree)
