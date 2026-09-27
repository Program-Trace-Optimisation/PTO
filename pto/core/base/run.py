from importlib import import_module
from .trace_operators import Op


def run(
    Gen,
    Fit,
    gen_args=(),
    fit_args=(),
    better=max,
    Solver="hill_climber",
    solver_args={},
    callback=None,
):
    """
    Configure and execute an optimization/search process.

    This function sets up a complete optimization by:
    1. Binding generator and fitness functions with their arguments
    2. Creating search operators for the specific problem
    3. Dynamically loading and configuring the requested solver
    4. Executing the optimization process

    Args:
        Gen: Generator class that creates solutions
        Fit: Fitness class that evaluates solutions
        gen_args: Tuple of arguments to pass to generator (default: ())
        fit_args: Tuple of arguments to pass to fitness function (default: ())
        better: Function to determine better solution (default: max)
        Solver: Either solver class or name of solver to import (default: 'hill_climber')
        solver_args: Dictionary of arguments for solver configuration (default: {})
        callback: Optional function called during optimization to monitor progress (default: None)

    Returns:
        If Solver=='search_operators': Returns configured Op instance
        Otherwise: Returns result of optimization process

    Raises:
        ValueError: If specified solver cannot be imported

    Example:
        >>> result = run(
        ...     Gen=MyGenerator,
        ...     Fit=MyFitness,
        ...     gen_args=(param1, param2),
        ...     fit_args=(param3,),
        ...     better=max,
        ...     Solver='hill_climber',
        ...     solver_args={'max_evals': 1000},
        ...     callback=lambda x: print(f"Best: {x}")
        ... )
    """

    # Specialize generator and fitness (problem)
    def gen():
        return Gen(*gen_args)

    def fit(sol):
        return Fit(sol, *fit_args)

    # Bind search operators to problem
    op = Op(generator=gen, fitness=fit)

    # Search operators mode
    if Solver == "search_operators":
        return op

    # Import the solver dynamically
    if isinstance(Solver, str):
        module_name = f"pto.solvers.{Solver}"
        try:
            solver_module = import_module(module_name)
            Solver = getattr(solver_module, Solver)
        except ModuleNotFoundError as e:
            if e.name != module_name:
                raise  # the solver exists but one of its dependencies is missing
            raise ValueError(
                f"Unknown solver '{Solver}'. Make sure it exists in the solvers module."
            ) from None
        except AttributeError:
            raise ValueError(
                f"Solver module '{module_name}' does not define '{Solver}'."
            ) from None

    # Instantiate search algorithm and bind it to search operators
    alg = Solver(op, better=better, callback=callback, **solver_args)

    # Execute search algorithm
    return alg()
