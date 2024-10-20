
# this module contains our standard problems as classes
# it re-uses the code in the individual problem files, eg onemax.py
# this file can be run from the current directory with `python as_classes.py`
# however, it uses an import hack (see below) suggested by Claude
# TODO: a better solution might be __main__.py

try:
    # Use absolute imports for when the file is run as a script
    from pto.problems import (onemax, sphere, helloworld, tsp, 
                              symbolic_regression, grammatical_evolution, 
                              graph_evolution, neural_network)
except ImportError:
    # Use relative imports for when the file is imported as a module
    from . import (onemax, sphere, helloworld, tsp, 
                   symbolic_regression, grammatical_evolution, 
                   graph_evolution, neural_network)

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
        super().__init__()
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
        super().__init__()
        self.fitness = symbolic_regression.fitness
        self.generator = symbolic_regression.generator
        func_set = [('and', 2), ('or', 2), ('not', 1)]
        term_set = [f'x[{i}]' for i in range(n_vars)]
        self.gen_args = (func_set, term_set)
        self.fit_args = symbolic_regression.make_training_data(n_samples, n_vars, func_set, term_set) # return (X_train, y_train)
        self.better = symbolic_regression.better

class GrammaticalEvolution(Problem):
    def __init__(self, n_samples, n_vars):
        super().__init__()
        self.fitness = grammatical_evolution.fitness
        self.generator = grammatical_evolution.generator
        grammar = grammatical_evolution.grammar
        grammar['<varidx>'] = [[str(i)] for i in range(n_vars)]
        self.gen_args = (grammar, )
        self.fit_args = grammatical_evolution.make_training_data(n_samples, n_vars) # (X_train, y_train)
        self.better = grammatical_evolution.better
        
    
class GraphEvolution(Problem):
    def __init__(self):
        super().__init__()
        self.fitness = graph_evolution.fitness
        self.generator = graph_evolution.generator
        self.gen_args = (graph_evolution.N,)
        self.fit_args = (graph_evolution.target,)
        self.better = graph_evolution.better

class NeuralNetwork(Problem):
    def __init__(self, n_inputs, max_hidden, n_outputs, n_samples):
        super().__init__()
        self.fitness = neural_network.fitness
        self.generator = neural_network.generator
        self.gen_args = (n_inputs, max_hidden, n_outputs)
        # (X_train, y_train)
        self.fit_args = neural_network.make_training_data(n_samples, n_inputs, 
                                                          neural_network.target_function) 
        self.better = neural_network.better        

__all__ = ['OneMax', 'LeadingOnes', 'Sphere', 'HelloWorld', 'TSP', 
           'SymbolicRegression', 'GrammaticalEvolution', 'GraphEvolution',
           'NeuralNetwork']


if __name__ == "__main__":

    # this is to exercise the problems as classes, in particular polymorphic use

    from pto import run, rnd
    probs = [
        OneMax(10),
        HelloWorld(),
        Sphere(5),
        TSP(N=5),
        SymbolicRegression(30, 3),
        GrammaticalEvolution(30, 4)
    ]
    for prob in probs: 
        print(prob.__class__.__name__)
        x, fx = run(prob.generator, 
                    prob.fitness, 
                    better=prob.better, 
                    fit_args=prob.fit_args, 
                    gen_args=prob.gen_args,
                    Solver='hill_climber',
                    solver_args=dict(n_generation=1000))
        print(x.pheno)
        print(fx)