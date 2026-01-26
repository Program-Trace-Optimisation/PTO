# this module contains our standard problems as classes
# it re-uses the code in the individual problem files, eg onemax.py
# these classes are intended to be useful for large factorial experiments
# whereas the standard problem .py files are intended as standalone examples.
# so, for example, these classes include information on the average and optimum
# fitness on a problem instance, and the size of the optimum trace.
# these classes expose a nice interface
# for polymorphic use in experiments.
# they include random generation of problem instances.

# for testing, this file can be run from the current directory with
# `python as_classes.py`
# however, it uses an import hack (see below) suggested by Claude
# TODO: a better solution might be __main__.py


from pto import run, rnd

# from pto.core import Random_cat
# from pto.core import choice
from statistics import mean
import numpy as np  # used in TSP
import math

try:
    # Use absolute imports for when the file is run as a script
    from pto.problems import (
        onemax,
        sphere,
        helloworld,
        tsp,
        k_tsp,
        assignment,
        symbolic_regression,
        grammatical_evolution,
        graph_evolution,
        neural_network,
    )
except ImportError:
    # Use relative imports for when the file is imported as a module
    from . import (
        onemax,
        sphere,
        helloworld,
        tsp,
        k_tsp,
        assignment,
        symbolic_regression,
        grammatical_evolution,
        graph_evolution,
        neural_network,
    )


class Problem:
    def __init__(self):
        self.gen_args = tuple()
        self.fit_args = tuple()
        self.better = max

    def estimate_average_fitness(self, n_samples=1000):
        """Use a simple random sample to estimate the average fitness
        on this problem instance. This is useful for providing
        normalised fitness values."""
        samples = (
            self.fitness(self.generator(*self.gen_args), *self.fit_args)
            for _ in range(n_samples)
        )
        self.average_fitness = mean(samples)

    def normalise_fitness(self, sol_fitness):
        """Normalise a given solution's fitness value on this problem instance, taking
        advantage of the instance's average fitness and its optimum fitness."""
        if self.better is min:
            return (self.average_fitness - sol_fitness) / (
                self.average_fitness - self.opt_fitness
            )
        elif self.better is max:
            return (sol_fitness - self.average_fitness) / (
                self.opt_fitness - self.average_fitness
            )
        else:
            raise ValueError(f"Unexpected better function {self.better}")

    def estimate_effective_dimensionality_and_budget(self, opt_trace):
        """Given the optimum trace which is provided as an argument,
        estimate the effective dimensionality of the space we are searching in,
        near to the optimum. Using that, calculate a fitness evaluation budget.
        We might need that budget eg for use in experiments.

        The trace `opt_trace` doesn't really have to be the optimum trace.
        It just has to be the same size as the optimum trace for this instance.

        The thinking here is that for some problems, the distribution of trace
        sizes is highly skewed, eg in Symbolic Regression, random sampling with
        a `grow`-style generator may give many very small trees. The optimum
        is probably not so small. So the distribution of trace sizes is not a good
        representation of the space that the solver is really searching in.

        A combinatorial space, such as a space of trees, does not have a dimensionality
        per se. By "effective dimensionality", we mean the dimensionality of a Cartesian space
        which is approximately the same size, locally, as the space.
        """

        op = run(
            self.generator,
            self.fitness,
            gen_args=self.gen_args,
            Solver="search_operators",
            dist_type="fine",
            name_type="lin",
            fit_args=self.fit_args,
            better=self.better,
        )

        opt_sol = op.fix_ind(opt_trace)
        n = op.space_dimension_ind(opt_sol)
        N = n**2
        return n, N


class OneMax(Problem):
    def __init__(self, N):
        super().__init__()
        self.gen_args = (N,)
        self.generator = onemax.generator
        self.fitness = onemax.fitness
        self.better = onemax.better
        self.opt_fitness = N
        self.estimate_average_fitness()


class LeadingOnes(OneMax):
    def __init__(self, N):
        super().__init__(N)
        self.estimate_average_fitness()

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
        self.opt_fitness = 0.0
        self.estimate_average_fitness()


class HelloWorld(Problem):
    def __init__(self, target=helloworld.target, alphabet=helloworld.alphabet):
        self.generator = helloworld.generator
        self.fitness = helloworld.fitness
        self.gen_args = (len(target), alphabet)
        self.fit_args = (target,)
        self.better = helloworld.better
        self.opt_fitness = len(target)
        self.estimate_average_fitness()


class TSP(Problem):
    def __init__(self, D=None, N=None, random_state=None):
        # pass in a distance matrix D, or else a size N and we will generate a random D
        super().__init__()
        if (D is None and N is None) or (D is not None and N is not None):
            raise ValueError(
                "Bad arguments: pass exactly 1 of distance matrix D or random instance size N"
            )
        if random_state is not None and N is None:
            raise ValueError(
                "Bad arguments: if passing random_state, must pass random instance size N"
            )
        if N is not None:
            D = tsp.make_problem_data(N, random_state)
        self.fitness = tsp.fitness
        self.generator = tsp.generator
        self.gen_args = (N,)
        self.fit_args = (D,)
        self.better = tsp.better
        self.opt_fitness = np.sum(
            np.min(D, axis=0)
        )  # under-estimate: if we could choose the min dist of each row
        self.estimate_average_fitness()


class kTSP(Problem):
    def __init__(self, D=None, N=None, k=None, random_state=None):
        # pass in a distance matrix D, or else a size N and city visit requirement k, and we will generate a random D
        super().__init__()
        if (D is None and N is None) or (D is not None and N is not None):
            raise ValueError(
                "Bad arguments: pass exactly 1 of distance matrix D or random instance size N"
            )
        if random_state is not None and N is None:
            raise ValueError(
                "Bad arguments: if passing random_state, must pass random instance size N"
            )
        if N is not None:
            D = k_tsp.make_problem_data(N, random_state)
        self.fitness = k_tsp.fitness
        self.generator = k_tsp.generator
        self.gen_args = (N, k)
        self.fit_args = (k, D)
        self.better = k_tsp.better
        self.opt_fitness = np.sum(
            np.min(D, axis=0)
        )  # under-estimate: if we could choose the min dist of each row
        self.estimate_average_fitness()


class Assignment(Problem):
    def __init__(self, cost_matrix=None, resource_matrix=None, agent_capacities=None, 
                 num_agents=None, num_tasks=None, 
                 random_state=None):
        # pass in either the problem data (cost matrix, resource marix, agent capacities)
        # OR the num_agents and num_tasks and we will generate the problem data
        super().__init__()
        if ((cost_matrix is None and num_agents is None) or 
            (cost_matrix is not None and num_agents is not None)):
            raise ValueError(
                "Bad arguments: pass problem data or problem size, not neither and not both"
            )
        if random_state is not None and num_agents is None:
            raise ValueError(
                "Bad arguments: if passing random_state, must pass random instance size num_agents and num_tasks"
            )
        if num_agents is not None:
            if num_tasks is None:
                num_tasks = num_agents * 2
            cost_matrix, resource_matrix, agent_capacities = assignment.generate_gap_instance(num_agents, num_tasks)
        self.fitness = assignment.fitness
        self.generator = assignment.generator_native
        self.gen_args = (num_agents, num_tasks)
        self.fit_args = (cost_matrix, resource_matrix, agent_capacities)
        self.better = assignment.better
        self.opt_fitness = np.sum(
            np.min(cost_matrix, axis=0)
        )  # under-estimate: if we could choose the min dist of each row
        self.estimate_average_fitness()

class SymbolicRegression(Problem):
    def __init__(self, n_samples, n_vars, target_gen=None, cnf_clause_len=None):
        super().__init__()
        if target_gen is None: target_gen = symbolic_regression.cnf_generator
        self.fitness = symbolic_regression.fitness
        self.generator = symbolic_regression.generator
        func_set = [("and", 2), ("or", 2), ("not", 1)]
        term_set = [f"x[{i}]" for i in range(n_vars)]
        max_depth = 1 + math.ceil(math.log2(len(term_set)))
        self.gen_args = (func_set, term_set, max_depth)
        self.fit_args = symbolic_regression.make_training_data(
            n_samples, n_vars, func_set, term_set, target_gen, cnf_clause_len=cnf_clause_len
        )
        self.better = symbolic_regression.better
        self.opt_fitness = 0.0
        self.estimate_average_fitness()

class BFSCNF(Problem):
    def __init__(self, n_vars, target_gen=None, clause_len=None):
        super().__init__()
        if target_gen is None: target_gen = symbolic_regression.cnf_generator
        self.fitness = symbolic_regression.balanced_fitness
        self.generator = symbolic_regression.generator
        func_set = [("and", 2), ("or", 2), ("not", 1)]
        term_set = [f"x[{i}]" for i in range(n_vars)]
        max_depth = 1 + math.ceil(math.log2(len(term_set)))
        self.gen_args = (func_set, term_set, max_depth)
        self.fit_args = symbolic_regression.make_critical_training_data_cnf(
            n_vars, clause_len=clause_len
        )
        self.better = symbolic_regression.better
        self.opt_fitness = 0.0
        self.estimate_average_fitness()


class GrammaticalEvolution(Problem):
    def __init__(self, n_samples, n_vars):
        super().__init__()
        self.fitness = grammatical_evolution.fitness
        self.generator = grammatical_evolution.generator
        grammar = grammatical_evolution.grammar
        grammar["<varidx>"] = [[str(i)] for i in range(n_vars)]
        self.gen_args = (grammar,)
        self.fit_args = grammatical_evolution.make_training_data(
            n_samples, n_vars
        )  # (X_train, y_train)
        self.better = grammatical_evolution.better
        self.opt_fitness = 0.0
        self.estimate_average_fitness()


class GraphEvolution(Problem):
    def __init__(self):
        super().__init__()
        self.fitness = graph_evolution.fitness
        self.generator = graph_evolution.generator
        self.gen_args = (graph_evolution.N,)
        self.fit_args = (graph_evolution.target,)
        self.better = graph_evolution.better
        self.opt_fitness = 0
        self.estimate_average_fitness()


class NeuralNetwork(
    Problem
):  # generate random weight matrices with max_hidden size # maybe use Numpy after all TODO
    def __init__(self, n_inputs, max_hidden, n_outputs, n_samples):
        super().__init__()
        self.fitness = neural_network.fitness
        self.generator = neural_network.generator
        self.gen_args = (n_inputs, max_hidden, n_outputs)
        # (X_train, y_train)
        self.fit_args = neural_network.make_training_data(n_samples, n_inputs)
        self.better = neural_network.better
        self.opt_fitness = 0.0
        self.estimate_average_fitness()


__all__ = [
    "OneMax",
    "LeadingOnes",
    "Sphere",
    "HelloWorld",
    "TSP",
    "kTSP",
    "Assignment",
    "SymbolicRegression",
    "GrammaticalEvolution",
    "GraphEvolution",
    "NeuralNetwork",
]


if __name__ == "__main__":

    # this is to exercise the problems as classes, in particular polymorphic use

    from pto import run, rnd

    probs = [
        OneMax(10),
        HelloWorld(),
        Sphere(5),
        TSP(N=5),
        kTSP(N=15, k=5),
        Assignment(num_agents=5, num_tasks=10),
        SymbolicRegression(30, 3),
        GrammaticalEvolution(30, 4),
    ]
    for prob in probs:
        print(prob.__class__.__name__)
        x, fx, gen = run(
            prob.generator,
            prob.fitness,
            better=prob.better,
            fit_args=prob.fit_args,
            gen_args=prob.gen_args,
            Solver="hill_climber",
            solver_args=dict(n_generation=1000),
        )
        print(x.pheno)
        print(x.geno)
        print(fx)
