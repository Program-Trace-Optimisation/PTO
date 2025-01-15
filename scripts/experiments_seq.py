from random import random, choice, randint, randrange, uniform, seed
import pandas as pd
import numpy as np
import math
import time
from multiprocessing import Pool

from pto import run, rnd

from pto.problems.as_classes import (
    OneMax, Sphere, HelloWorld,
    TSP, kTSP, Assignment,
    SymbolicRegression, GrammaticalEvolution, NeuralNetwork,
)
from pto.problems.tsp import (generator_native as tsp_gen_native, generator_knuth as tsp_gen_knuth, generator_pmx as tsp_gen_pmx)
from pto.problems.k_tsp import (generator_native as ktsp_gen_native, generator_sim_knuth as ktsp_gen_sim_knuth, generator_sim_remove as ktsp_gen_sim_remove)
from pto.problems.assignment import (generator_native as gap_gen_native, generator_simulated as gap_gen_sim)


solvers = [
    "random_search",
    "hill_climber",
    "genetic_algorithm",
    # "particle_swarm_optimisation" # not used for seq experiments
]

def solvers_argss(solver, budget):
    d = {
        "random_search": 
        {'n_generation': budget},
        "hill_climber": 
        {'n_generation': budget},
        "genetic_algorithm": 
        {'n_generation': int(math.sqrt(budget)), 
         'population_size': int(budget / int(math.sqrt(budget)))},
        "particle_swarm_optimisation": 
        {'n_iteration': int(math.sqrt(budget) / 4), 
         'n_particles': int(budget / (math.sqrt(budget) / 4))}
    }
    result = d[solver]
    result['return_history'] = True
    return result

problems_sizess_budgetss_ctors = [
        # each row is (problem_name, sizes, constructor fn given only size)
        ('OneMax', (8, 16, 32), (50, 200, 1000), (lambda s: OneMax(s))),
        ('HelloWorld', (8, 16, 32), (500, 2000, 6000), (lambda s: HelloWorld(target='A'*s))),
        ('Sphere', (8, 16, 32), (100, 500, 5000), (lambda s: Sphere(s))),
        ('TSP', (8, 16, 24), (5000, 50000, 100000), (lambda s: TSP(N=s))), 
        ('kTSP', (20, 40, 60), (10000, 30000, 100000), (lambda s: kTSP(N=s, k=s // 4))), # choose k cities from N
        ('Assignment', (10, 20, 30), (10000, 30000, 100000), (lambda s: Assignment(num_agents=s))),
        ('SymbolicRegression', (6, 9, 12), (8000, 20000, 100000), (lambda s: SymbolicRegression(s*20, s))), 
        ('GrammaticalEvolution', (3, 6, 9), (2000, 10000, 30000), (lambda s: GrammaticalEvolution(s*20, s))), 
        ('NeuralNetwork', (2, 4, 6), (3000, 10000, 50000), (lambda s: NeuralNetwork(s, int(s*1.5), s, s*20))) # s*1.5 is the max_hidden
]

crossovers = ['crossover_one_point_ind', 'crossover_uniform_ind']

generators = {
    "TSP": [tsp_gen_native, tsp_gen_knuth, tsp_gen_pmx],
    "kTSP": [ktsp_gen_native, ktsp_gen_sim_knuth, ktsp_gen_sim_remove],
    "Assignment": [gap_gen_native, gap_gen_sim]
}

def run_one_rep(rep):
    results = []
    for problem_name, sizes, budgets, ctor in problems_sizess_budgetss_ctors:    
        for size, budget, size_cat in zip(sizes, budgets, ["small", "medium", "large"]):

            print(problem_name, size, budget)
            problem = ctor(size)

            # this code could be used in future for estimation of effective dimensionality
            # opt_trace = problem_sizes_opt_traces[problem_name][size]
            # dim, budget = problem.estimate_effective_dimensionality_and_budget(opt_trace)
            # print(problem_name, size, dim, budget) 
            
            for solver in solvers:

                solver_args = solvers_argss(solver, budget)
                for dist_type in ['coarse', 'fine']:
                    for name_type in ['lin', 'str']:
                        
                        for xover in crossovers:

                            # if we are not running GA, crossover has no effect,
                            # so don't run both crossovers. it doesn't matter which we run.
                            # the parameter name xover = "crossover_uniform_ind" will be
                            # recorded but for RS, HC, we should just ignore that parameter 
                            # in the results.
                            if solver != "genetic_algorithm":
                                if xover != "crossover_uniform_ind":
                                    continue

                            if solver == "genetic_algorithm":
                                solver_args['crossover'] = xover

                            for generator in generators[problem_name]:

                                seed(rep) # random.seed(rep)
                                start_time = time.time()
                                (pheno, geno), fx, history = run(generator, 
                                                    problem.fitness, 
                                                    gen_args=problem.gen_args, 
                                                    fit_args=problem.fit_args,
                                                    Solver=solver,
                                                    solver_args=solver_args,
                                                    better=problem.better,
                                                    dist_type=dist_type,
                                                    name_type=name_type)

                                end_time = time.time()
                                elapsed = end_time - start_time
                                norm_fx = problem.normalise_fitness(fx)

                                filename = f'outputs/history_{problem.__class__.__name__} {size} {size_cat} {solver} {budget} {dist_type} {name_type} {xover} {generator.__name__} {rep}'.replace(' ', '_')
                                history_df = pd.DataFrame(history, columns=['fitness'])
                                history_df.to_csv(filename)

                                # we're not printing or saving gen_args - maybe we should? but they are large matrices, not just keywords
                                print(f'{problem.__class__.__name__} {size} {size_cat} {solver} {budget} {dist_type} {name_type} {xover} {generator.__name__} {rep} {elapsed} {fx} {norm_fx} "{pheno}" "{geno}"')
                                results.append((problem.__class__.__name__, size, size_cat, solver, budget, dist_type, name_type, xover, generator.__name__, rep, elapsed, fx, norm_fx, str(pheno), str(geno)))

    columns = "problem size size_cat solver budget dist_type name_type xover generator rep elapsed fx norm_fx pheno geno".split(" ")
    df = pd.DataFrame.from_records(columns=columns, data=results)
    return df
    

if __name__ == '__main__':
    n_reps = 30
    with Pool() as pool:
        results_dfs = pool.map(run_one_rep, range(n_reps))
        combined_df = pd.concat(results_dfs, ignore_index=True)
    combined_df.to_csv('outputs/results_2025_01_15_seq_native.csv')
