
from ...solvers import HC

from .trace_operators import Op

class CoreRunner:
    @classmethod
    def run(cls, Gen, Fit, gen_args=(), fit_args=(), better=max, Solver=HC, solver_args={}, callback=None):
    
        # specialise generator and fitness (problem)
        def gen(): return Gen(*gen_args)
        def fit(sol): return Fit(sol, *fit_args)
    
        # bind search operators to problem
        op = Op(generator=gen, fitness=fit)
    
        # instantiate search algorithm and bind it to searh operators
        alg = Solver(op, better=better, callback=callback, **solver_args)
    
        # execute search algorithm
        return alg()

run = CoreRunner.run

