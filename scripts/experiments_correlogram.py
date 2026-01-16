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

from pto.problems.onemax import generator as onemax_gen
from pto.problems.sphere import generator as sphere_gen
from pto.problems.symbolic_regression import generator as sr_gen, generator_depth as sr_depth_gen
from pto.problems.symbolic_regression import cnf_generator as sr_target_cnf, full as sr_target_full, even_parity as sr_evenparity_gen

# Simulated Annealing as the only solver because it is simple, generic, reliable
# no crossover
# 1 generator per problem
# 1 mutation
# 1 distance
# 3 sizes
# 2 name types, 2 dist types
# try random sampling versus random walk as correlogram walks


problems_sizess_budgetss_ctors = [
        # each row is (problem_name, sizes, budgets, constructor fn given only size)
        ('OneMax', (8, 16, 32), (50, 200, 1000), (lambda s: OneMax(s))),
        # ('HelloWorld', (8, 16, 32), (500, 2000, 6000), (lambda s: HelloWorld(target='A'*s))),
        ('Sphere', (8, 16, 32), (100, 500, 5000), (lambda s: Sphere(s))),
        # ('TSP', (8, 16, 24), (5000, 50000, 100000), (lambda s: TSP(N=s))), 
        # ('kTSP', (20, 40, 60), (10000, 30000, 100000), (lambda s: kTSP(N=s, k=s // 4))), # choose k cities from N
        # ('Assignment', (10, 20, 30), (10000, 30000, 100000), (lambda s: Assignment(num_agents=s))),

        # several different problems in boolean function synthesis. two sets of synthetic problems, and even-parity
        ('BFS-CNF', (6, 9, 12), (8000, 20000, 100000), (lambda s: SymbolicRegression(s*20, s, target_gen=sr_target_cnf))), 
        ('BFS-Full', (6, 9, 12), (8000, 20000, 100000), (lambda s: SymbolicRegression(s*20, s, target_gen=sr_target_full))), 
        ('BFS-EvenParity', (6, 9, 12), (8000, 20000, 100000), (lambda s: SymbolicRegression(s*20, s, target_gen=sr_evenparity_gen))),
        #('GrammaticalEvolution', (3, 6, 9), (2000, 10000, 30000), (lambda s: GrammaticalEvolution(s*20, s))), 
        #('NeuralNetwork', (2, 4, 6), (3000, 10000, 50000), (lambda s: NeuralNetwork(s, int(s*1.5), s, s*20))) # s*1.5 is the max_hidden
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

size_cats = ["small", "medium", "large"]
# size_cats = ['small', 'medium'] # for testing

# PTO generators (not target generators)
generators = {
    "OneMax": (onemax_gen,),
    "Sphere": (sphere_gen,),
    "BFS-CNF": (sr_gen, sr_depth_gen),
    "BFS-Full": (sr_gen, sr_depth_gen),
    "BFS-EvenParity": (sr_gen, sr_depth_gen),
}

def run_one_correlogram_rep(rep):
    results = []
    results = []

    for problem_name, sizes, budgets, ctor in problems_sizess_budgetss_ctors:
        for size, budget, size_cat in zip(sizes, budgets, size_cats):

            print(problem_name, size, budget)
            problem = ctor(size)

            for solver in ["correlogram"]: # a dummy "solver"
                solver_args = {'avg_dist_tolerance': 0.1, 'n_walks': 5, 'verbose': True} # any other args needed for correlogram? 
                for dist_type in ['coarse']: # ['coarse', 'fine']:
                    for name_type in ['lin', 'str']:
                        for generator in generators[problem_name]:
                            if generator == onemax_gen:
                                generator_name = "one-max"
                            elif generator == sphere_gen:
                                generator_name = "sphere-gen"
                            elif generator == sr_gen:
                                generator_name = "sr-gen"
                            elif generator == sr_depth_gen:
                                generator_name = "sr-depth-gen"
                            else:
                                raise ValueError("Unexpected generator")

                            # RUN correlogram
                            seed(rep) # random.seed(rep)
                            start_time = time.time()
                            x_axis, y_axis, p_axis, n_axis, cor_length, diameter, onestep_cor = run(generator,
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

                            # Save x_axis, y_axis, p_axis, and n_axis to CSV
                            csv_filename = f'outputs/results_2026_01_07_correlogram_xy_{problem_name}_{size}_{size_cat}_{budget}_{dist_type}_{name_type}_{generator_name}_rep{rep}.csv'
                            xy_df = pd.DataFrame({'x_axis': x_axis, 'y_axis': y_axis, 'p_axis': p_axis, 'n_axis': n_axis})
                            xy_df.to_csv(csv_filename, index=False)

                            print(f'{problem_name} {size} {size_cat} {solver} {budget} {dist_type} {name_type} {generator_name} {rep} {elapsed} {cor_length} {onestep_cor} {diameter}')
                            results.append((problem_name, size, size_cat, solver, budget, dist_type, name_type, generator_name, rep, elapsed, cor_length, onestep_cor, diameter))

    columns = "problem size size_cat solver budget dist_type name_type generator rep elapsed cor_length onestep_cor diameter".split(" ")
    df = pd.DataFrame.from_records(columns=columns, data=results)
    return df                

def run_one_solver_rep(rep):
    results = []

    for problem_name, sizes, budgets, ctor in problems_sizess_budgetss_ctors:    
        for size, budget, size_cat in zip(sizes, budgets, size_cats):

            print(problem_name, size, budget)
            problem = ctor(size)

            budget = 100

            for solver in ["random_search", "hill_climber", "genetic_algorithm"]: 
                solver_args = solvers_argss(solver, budget)
                for dist_type in ['coarse']: # ['coarse', 'fine']:
                    for name_type in ['lin', 'str']:
                        for generator in generators[problem_name]:
                        

                            # RUN SA
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

                            filename = f'outputs/history_{problem.__class__.__name__}_{size}_{size_cat}_{solver}_{budget}_{dist_type}_{name_type}_{generator.__name__}_{rep}.pdf'.replace(' ', '_')
                            history_df = pd.DataFrame(history, columns=['fitness'])
                            history_df.to_csv(filename)

                            print(f'{problem.__class__.__name__} {size} {size_cat} {solver} {budget} {dist_type} {name_type} {generator.__name__} {rep} {elapsed} {fx} {norm_fx} "{pheno}" "{geno}"')
                            results.append((problem.__class__.__name__, size, size_cat, solver, budget, dist_type, name_type, generator.__name__, rep, elapsed, fx, norm_fx, str(pheno), str(geno)))


    columns = "problem size size_cat solver budget dist_type name_type generator rep elapsed fx norm_fx pheno geno".split(" ")
    df = pd.DataFrame.from_records(columns=columns, data=results)
    return df
    

if __name__ == '__main__':
    # Test autocorrelation analysis
    df = run_one_correlogram_rep(0)
    df.to_csv('outputs/results_2026_01_07_correlogram.csv')
    import sys; sys.exit()

    n_reps = 10
    # with Pool() as pool:
    #     results_dfs = pool.map(run_one_solver_rep, range(n_reps))
    #     combined_df = pd.concat(results_dfs, ignore_index=True)
    # combined_df.to_csv('outputs/results_2026_01_07_correlogram_solver.csv')
    with Pool() as pool:
        results_dfs = pool.map(run_one_correlogram_rep, range(n_reps))
        combined_df = pd.concat(results_dfs, ignore_index=True)
    combined_df.to_csv('outputs/results_2026_01_07_correlogram.csv')
 

