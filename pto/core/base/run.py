
from importlib import import_module
from .trace_operators import Op

class CoreRunner:
    @classmethod
    def run(cls, Gen, Fit, gen_args=(), fit_args=(), better=max, Solver='hill_climber', solver_args={}, callback=None):
                
        # specialise generator and fitness (problem)
        def gen(): return Gen(*gen_args)
        def fit(sol): return Fit(sol, *fit_args)
    
        # bind search operators to problem
        op = Op(generator=gen, fitness=fit)

        # search opertaors mode
        if Solver == 'search_operators':
            return op

        # import the solver dynamically
        if isinstance(Solver, str):
            try:
                solver_module = import_module(f'...solvers.{Solver}', package=__package__)
                Solver = getattr(solver_module, Solver)
            except (ImportError, AttributeError):
                raise ValueError(f"Unable to import solver '{Solver}'. Make sure it exists in the solvers module.")
    
        # instantiate search algorithm and bind it to search operators
        alg = Solver(op, better=better, callback=callback, **solver_args)
    
        # execute search algorithm
        return alg()

run = CoreRunner.run