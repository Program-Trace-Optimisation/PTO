from random import random, choice, randint, randrange, uniform, seed
import pandas as pd
import numpy as np
import math
import time
from multiprocessing import Pool
import matplotlib.pyplot as plt


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

# RS, HC, GA
# 1 generator per problem
# (3 distinct problem-generators for BFS)
# 1 mutation
# 1 distance
# 3 sizes
# 2 name types
# 1 dist type
# try random sampling versus random walk as correlogram walks

# ('HelloWorld', (8, 16, 32), (500, 2000, 6000), (lambda s: HelloWorld(target='A'*s))),
        # ('Sphere', (10, 20, 40), (10000, 50000, 200000), (lambda s: Sphere(s))),
problems_sizess_budgetss_ctors = [
        # each row is (problem_name, sizes, budgets, constructor fn given only size)
        ('OneMax', (10, 50, 100), (10000, 50000, 200000), (lambda s: OneMax(s))),

        # several different problems in boolean function synthesis. two sets of synthetic problems, and even-parity
        ('BFS-CNF', (6, 12, 18), (10000, 50000, 200000), (lambda s: SymbolicRegression(s*20, s, target_gen=sr_target_cnf))), 
        ('BFS-Full', (6, 12, 18), (10000, 50000, 200000), (lambda s: SymbolicRegression(s*20, s, target_gen=sr_target_full))), 
        ('BFS-EvenParity', (6, 12, 18), (10000, 50000, 200000), (lambda s: SymbolicRegression(s*20, s, target_gen=sr_evenparity_gen))),
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
    "BFS-CNF": (sr_depth_gen,),
    "BFS-Full": (sr_depth_gen,),
    "BFS-EvenParity": (sr_depth_gen,),
}

def run_one_correlogram_rep(rep):
    results = []
    results = []

    for problem_name, sizes, budgets, ctor in problems_sizess_budgetss_ctors:
        for size, budget, size_cat in zip(sizes, budgets, size_cats):

            print("CORRELATION", "rep", rep, problem_name, size)
            problem = ctor(size)

            if "BFS" in problem_name:
                assert size % 3 == 0 # symbolic_regression.py (BFS) generators assume this

            for solver in ["correlogram"]: # a dummy "solver"
                solver_args = {'avg_dist_tolerance': 0.1, 'n_samples': 1000, 'n_walks': 20, 'verbose': True} # any other args needed for correlogram?
                if "BFS" in problem_name:
                    solver_args['run_structural_mutation_filter'] = True 
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
                            (x_axis, y_axis, p_axis, n_axis, 
                             cor_length, diameter, onestep_cor, 
                             sr_structural_change_cor, sr_average_parent_length,
                              g_avg_dist, g_total_var, g_norm_corr_length, g_nugget,
                              variogram, dist_matrix, fitvals) = run(generator,
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
                            # save distances for later use in variogram
                            dist_filename = csv_filename[:-4] + ".npy"
                            np.save(dist_filename, dist_matrix)
                            fit_filename = csv_filename[:-4] + "_fitness.npy"
                            np.save(fit_filename, fitvals)

                            print(f'{problem_name} {size} {size_cat} {solver} {budget} {dist_type} {name_type} {generator_name} {rep} {elapsed} {cor_length} {onestep_cor} {diameter} {sr_structural_change_cor} {sr_average_parent_length} {g_avg_dist} {g_total_var} {g_norm_corr_length} {g_nugget}')
                            results.append((problem_name, size, size_cat, solver, budget, dist_type, name_type, generator_name, rep, elapsed, cor_length, onestep_cor, diameter, sr_structural_change_cor, sr_average_parent_length, g_avg_dist, g_total_var, g_norm_corr_length, g_nugget))

    columns = "problem size size_cat solver budget dist_type name_type generator rep elapsed cor_length onestep_cor diameter sr_structural_change_cor sr_average_parent_length g_avg_dist g_total_var g_norm_corr_length g_nugget".split(" ")
    df = pd.DataFrame.from_records(columns=columns, data=results)
    return df                

def run_one_solver_rep(rep):
    results = []

    for problem_name, sizes, budgets, ctor in problems_sizess_budgetss_ctors:    
        for size, budget, size_cat in zip(sizes, budgets, size_cats):

            print(problem_name, size, budget)
            problem = ctor(size)

            def make_callback(better=min, pop_based=False, n_iters_no_improve=100):
                history = []
                def terminate_opt_no_improve(search_state):

                    # update state
                    if pop_based:
                        population, fitness_population, gen = search_state
                        fitness_individual = better(fitness_population)
                    else:
                        individual, fitness_individual, gen = search_state
                    history.append(fitness_individual)

                    # check for early termination
                    if fitness_individual == problem.opt_fitness:
                        return True
                    if len(history) > n_iters_no_improve:
                        if len(set(fit for fit in history[-n_iters_no_improve:])) == 1:
                            return True
                    return False
                return terminate_opt_no_improve

            for solver in ["genetic_algorithm", "random_search", "hill_climber"]: 
                solver_args = solvers_argss(solver, budget)

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
                            
                            if solver == 'genetic_algorithm' or solver == 'particle_swarm_optimisation':
                                # stop if no improvement during a segment of length 50% of the run

                                # history counted in generations
                                callback = make_callback(problem.better, pop_based=True, 
                                                         n_iters_no_improve=10000000) # no early stopping
                            else:
                                # history counted in individuals
                                callback = make_callback(problem.better, pop_based=False, 
                                                         n_iters_no_improve=10000000) # no early stopping

                            # unnecessary combination
                            if solver == 'random_search':
                                if name_type == 'str': continue
                                if dist_type == 'fine': continue

                            # hacks for quick investigation runs

                            # if dist_type != 'coarse': continue
                            # if name_type != 'str': continue
                            # if problem_name != 'OneMax': continue
                            # if size_cat != "small": continue
                            # if solver != 'hill_climber': continue
                            # if generator != onemax_gen: continue                        
                        

                            # RUN solver
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
                                                             name_type=name_type,
                                                             callback=callback,
                            )

                            end_time = time.time()
                            elapsed = end_time - start_time
                            norm_fx = problem.normalise_fitness(fx)
                            geno_size = len(geno)
                            hist_len = len(history)

                            # Downsample history for hill_climber and random_search to avoid huge files
                            if solver in ['hill_climber', 'random_search']:
                                history_to_save = downsample_history(history, max_samples=1000)
                            else:
                                history_to_save = history

                            filename = f'outputs/history_{problem_name}_{size}_{size_cat}_{solver}_{budget}_{dist_type}_{name_type}_{generator_name}_{rep}.csv'.replace(' ', '_')
                            history_df = pd.DataFrame(history_to_save, columns=['fitness'])
                            history_df.to_csv(filename)

                            print(f'{problem_name} {size} {size_cat} {solver} {budget} {dist_type} {name_type} {generator_name} {rep} {elapsed} {fx} {norm_fx} {geno_size} {hist_len} "{pheno}" "{geno}"')
                            results.append((problem_name, size, size_cat, solver, budget, dist_type, name_type, generator_name, rep, elapsed, fx, norm_fx, geno_size, hist_len, str(pheno), str(geno)))


    columns = "problem size size_cat solver budget dist_type name_type generator rep elapsed fx norm_fx geno_size hist_len pheno geno".split(" ")
    df = pd.DataFrame.from_records(columns=columns, data=results)
    return df



def downsample_history(history, max_samples=1000):
    """
    Downsample history to at most max_samples, always keeping first and last values.

    Args:
        history: list of fitness values
        max_samples: maximum number of samples to keep

    Returns:
        downsampled list of fitness values
    """
    if len(history) <= max_samples:
        return history

    # Always keep first and last
    downsampled = [history[0]]

    # Sample evenly from the middle
    # We need (max_samples - 2) samples from the middle
    middle_samples = max_samples - 2
    indices = np.linspace(1, len(history) - 2, middle_samples, dtype=int)

    for idx in indices:
        downsampled.append(history[idx])

    # Add the last value
    downsampled.append(history[-1])

    return downsampled
    

if __name__ == '__main__':
    # # Test autocorrelation analysis
    df = run_one_correlogram_rep(0)
    df.to_csv('outputs/results_2026_01_07_correlogram.csv')
    import sys; sys.exit()

    # df = run_one_solver_rep(0)

    # n_reps = 20
    # import os
    # with Pool(processes=os.cpu_count() - 1) as pool:
    #     results_dfs = pool.map(run_one_solver_rep, range(n_reps))
    #     combined_df = pd.concat(results_dfs, ignore_index=True)
    # combined_df.to_csv('outputs/results_2026_01_07_correlogram_solver.csv')
    # print(combined_df)

 

