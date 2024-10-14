from . import (
    onemax, 
    sphere, 
    helloworld, 
    tsp, 
    symbolic_regression, 
    grammatical_evolution, 
    graph_evolution,
)

class Problem:
    def __init__(self):
        self.gen_args = tuple()
        self.fit_args = tuple()
        self.better = max

class OneMax(Problem):
    def __init__(self, N):
        super().__init__()
        self.gen_args = (N,)
        self.generator = onemax.generator
        self.fitness = onemax.fitness
        self.better = onemax.better

class LeadingOnes(OneMax):
    def __init__(self, N):
        super().__init__(N)
    def fitness(self, sol):  
        val = 0
        for bit in sol:
            if bit == 0:
                break
            else:
                val += 1
        return val
    
class Sphere(Problem):
    def __init__(self, N):
        super().__init__()
        self.gen_args = (N,)
        self.generator = sphere.generator
        self.fitness = sphere.fitness
        self.better = sphere.better 

class HelloWorld(Problem):
    def __init__(self, target=helloworld.target, alphabet=helloworld.alphabet):
        self.generator = helloworld.generator
        self.fitness = helloworld.fitness
        self.gen_args = (len(target), alphabet)
        self.fit_args = (target,)
        self.better = helloworld.better

class TSP(Problem):
    def __init__(self, D=None, N=None, random_state=None):
        # pass in a distance matrix D, or else a size N and we will generate a random D
        if (D is None and N is None) or (D is not None and N is not None):
            raise ValueError("Bad arguments: pass exactly 1 of distance matrix D or random instance size N")
        if random_state is not None and N is None:
            raise ValueError("Bad arguments: if passing random_state, must pass random instance size N")
        if N is not None:
            D = tsp.make_problem_data(N, random_state)
        self.fitness = tsp.fitness
        self.generator = tsp.generator
        self.gen_args = (N,)
        self.fit_args = (D,)
        self.better = tsp.better     


class SymbolicRegression(Problem):
    def __init__(self, n_samples, n_vars):
        self.fitness = symbolic_regression.fitness
        self.generator = symbolic_regression.generator
        self.gen_args = (symbolic_regression.func_set, symbolic_regression.term_set)
        self.fit_args = symbolic_regression.make_training_data(n_samples, n_vars) # (X_train, y_train)
        self.better = symbolic_regression.better

class GrammaticalEvolution(Problem):
    def __init__(self, n_samples, n_vars):
        self.fitness = grammatical_evolution.fitness
        self.generator = grammatical_evolution.generator
        self.gen_args = (grammatical_evolution.grammar, )
        self.fit_args = grammatical_evolution.make_training_data(n_samples, n_vars) # (X_train, y_train)
        self.better = grammatical_evolution.better
        
    
class GraphEvolution(Problem):
    def __init__(self):
        self.fitness = graph_evolution.fitness
        self.generator = graph_evolution.generator
        self.gen_args = (graph_evolution.N,)
        self.fit_args = (graph_evolution.target,)
        self.better = graph_evolution.better

__all__ = ['OneMax', 'LeadingOnes', 'Sphere', 'HelloWorld']