"""run(): build a search space and run a solver on it."""

from dataclasses import dataclass
from importlib import import_module
from typing import Any, Optional

from .space import SearchSpace, Solution


@dataclass
class Result:
    """What a run found. Unpacks like the original PTO's run():
    (pheno, geno), fitness, generations = run(...), with the history in
    place of the generations when solver_args={'return_history': True}."""

    best: Solution
    fitness: Any
    generations: Optional[int] = None
    history: Optional[list] = None

    def __iter__(self):
        yield self.best
        yield self.fitness
        yield self.history if self.history is not None else self.generations


def solver_class(Solver):
    """A solver class, or the class named Solver in pto.solvers."""
    if not isinstance(Solver, str):
        return Solver
    module_name = f"pto.solvers.{Solver}"
    try:
        return getattr(import_module(module_name), Solver)
    except ModuleNotFoundError as e:
        if e.name != module_name:
            raise
        raise ValueError(f"Unknown solver {Solver!r}") from None


def run(
    generator,
    fitness,
    gen_args=(),
    fit_args=(),
    better=max,
    Solver="hill_climber",
    solver_args=None,
    callback=None,
    seed=None,
    naming="dynamic",
    operators="fine",
):
    """
    Run Solver on the problem given by generator and fitness.

    generator:   a function making random decisions with rnd
    fitness:     fitness(phenotype, *fit_args)
    better:      max or min
    Solver:      a solver class, or the name of one in pto.solvers
    solver_args: dict of arguments for the solver (n_generation, mutation, ...)
    callback:    passed to the solver
    seed:        makes the run reproducible (see SearchSpace for the random streams)
    naming:      'dynamic' (default), 'static' or 'linear'
    operators:   'fine' (default) or 'coarse'

    Returns a Result, or the SearchSpace itself with Solver='search_operators'.
    """
    solver_args = dict(solver_args or {})
    space = SearchSpace(
        generator, fitness, gen_args, fit_args, naming=naming, operators=operators, seed=seed,
    )
    if Solver == "search_operators":
        return space
    Solver = solver_class(Solver)
    best, fx, third = Solver(space, better=better, callback=callback, **solver_args)()
    if solver_args.get("return_history"):
        return Result(best, fx, history=third)
    return Result(best, fx, generations=third)
