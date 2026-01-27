import pandas as pd
import time
from datetime import datetime
from multiprocessing import Pool
import os
from random import seed as stdlib_seed

from lc import *
import lc
import lc_pto
from lc_pto import tuple_generator, debruijn_generator, probability, generic_fitness, unary_fitness, binop_fitness, list_fitness, fold_fitness, all_fitness, truth_tables
from lc_pto import SUCC_TRAINING_CASES, PLUS_TRAINING_CASES, IS_ZERO_TRAINING_CASES, FOLD_TRAINING_CASES, SUCC_TEST_CASES, PLUS_TEST_CASES, IS_ZERO_TEST_CASES
from lc_pto import apply_unary, apply_binop, apply_trinop

from pto import run


def terminate_on_success_callback(search_state):
    (individual, fitness, gen) = search_state
    try:
        if 0 in fitness or 0.0 in fitness: return True # GA gives the fitness of population as a list
    except:
        if fitness == 0: return True # HC gives the fitness of one individual
    return False

probabilities = {
    # problem name: probability
    'NOT' :    3.7633528463178407e-06,
    'AND' :    6.350657928161356e-06,
    'SUCC':    4.181503162575378e-07,
    'PLUS':    1.2250497546607553e-09,
    'IS_ZERO': 9.408382115794602e-07,
    'ALL':     2.7320263591606063e-16,
    'FOLD':    1.129005853895352e-05,
    # we have a value for LENGTH also

}

problems = { 
    # problem name: (max_depth, budget, fitcases, fitcases_test, apply)
    'NOT' :    (8,  30000,  truth_tables['NOT'], truth_tables['NOT'], apply_unary),
    'AND' :    (8,  10000,  truth_tables['AND'], truth_tables['AND'], apply_binop),
    'SUCC':    (10, 30000,  SUCC_TRAINING_CASES, SUCC_TEST_CASES, apply_unary),
    'PLUS':    (12, 1000000, PLUS_TRAINING_CASES, PLUS_TEST_CASES, apply_binop),
    'IS_ZERO': (10, 30000,  truth_tables['IS_ZERO'], truth_tables['IS_ZERO_TEST'], apply_unary),
    'ALL':     (12, 300000, truth_tables['ALL'], truth_tables['ALL_TEST'], apply_unary),
    'FOLD':    (12, 1000000, truth_tables['FOLD'], truth_tables['FOLD_TEST'], apply_trinop),
    'LENGTH':  (12, 30000, truth_tables['LENGTH'], truth_tables['LENGTH_TEST'], apply_unary),
}


def downsample_history_rs_hc(history, budget, popsize):
    # history is every individual from 0 up to eg budget=10000
    new = [] # start with zeros as our history may be truncated if we reach zero early
    for i, fx in enumerate(history):
        if i % popsize == 0:
            new.append((i, fx))
    return new

def multiply_history_ga(history, budget, popsize):
    # history is every generation
    # each generation represents popsize individuals so we multiply
    new = [] # start with zeros as our history may be truncated if we reach zero early
    for i, fx in enumerate(history):
        # multiply by 0, 1, 2, ...
        new.append((i * popsize, fx))
    return new


def run_one_rep(rep):

    stdlib_seed(rep)
    print(f"Worker {os.getpid()} starting rep {rep}")

    global MAX_DEPTH, MACROS_ENABLED
    
    rows = []
    for problem in problems:
        max_depth, budget, fitcases, fitcases_test, apply = problems[problem]

        # if problem not in ('LENGTH'): continue # NB only for current experiment

        # budget = 200 # NB only for tests

        MAX_DEPTH = lc.MAX_DEPTH = lc_pto.MAX_DEPTH = max_depth

        for generator in [tuple_generator, debruijn_generator]:

            # if generator == tuple_generator: continue # NB debruijn only in current run

            for solver in ['random_search', 'hill_climber', 'genetic_algorithm']:

                # if solver != 'hill_climber': continue
                
                popsize = 100 # just copying the ARC paper
                if solver == 'genetic_algorithm':
                    solver_args = {'n_generation': budget // popsize, 'population_size': popsize}
                else:
                    solver_args = {'n_generation': budget}
                solver_args['return_history'] = True


                dist_type = 'fine' # or coarse, but that's not of interest in LC
                for name_type in ('str', 'lin'):

                    # if name_type == 'lin': continue # NB str only for current experiment

                    for macros_enabled in [False, True]: 

                        if macros_enabled == True: continue # NB no macros for current experiment

                        # macros enabled only for a subset of problems
                        if macros_enabled == True and problem not in ('IS_ZERO', 'ALL'): continue

                        # don't write `for MACROS_ENABLED in [True, False]` as it creates a new variable
                        MACROS_ENABLED = lc.MACROS_ENABLED = lc_pto.MACROS_ENABLED = macros_enabled 

                        for metric in [shd, discrete_metric]:

                            # if metric == discrete_metric: continue # NB only shd for current experiment

                            # for RS, name type, dist type, and metric are irrelevant so do only one setup
                            if solver == 'random_search' and not (metric == discrete_metric and name_type == 'lin'): continue

                            fitness_fn = lambda expr: generic_fitness(expr, fitcases, apply, metric=metric)
                            fitness_fn_test = lambda expr: generic_fitness(expr, fitcases_test, apply, metric=discrete_metric)

                            # # Debug: test the fitness function directly
                            # test_expr = debruijn_generator()
                            # test_fitness = _fitness_fn(test_expr)
                            # print(f"Debug test fitness: {test_fitness}")
                            # return
                            start = time.time()
                            (pheno, geno), reported_fx, history = run(
                                generator, 
                                fitness_fn, 
                                better=min, 
                                Solver=solver,
                                solver_args=solver_args,
                                name_type=name_type,
                                callback=terminate_on_success_callback)
                            end = time.time()
                            elapsed = end - start

                            
                            if solver == 'hill_climber' or solver == 'random_search':
                                n_iterations = len(history) - 1
                                history = downsample_history_rs_hc(history, budget, popsize)
                            else:
                                n_iterations = (len(history) - 1) * popsize
                                history = multiply_history_ga(history, budget, popsize)


                            filename_base = f'{problem} {max_depth} {macros_enabled} {generator.__name__} {solver} {metric.__name__} {dist_type} {name_type} {rep}'.replace(' ', '_')
                            history_df = pd.DataFrame(history, columns=['Evaluations', 'Fitness'])
                            history_df.to_csv(f"outputs/histories/history_{filename_base}.csv")
                            open(f"outputs/phenotypes/phenotype_{filename_base}.py", 'w').write(str(pheno))

                            # final evaluation with discrete_metric as we only care about end result
                            final_fx = fitness_fn_test(pheno) 

                            # print the result for this run 
                            csv_tuple = (problem, max_depth, macros_enabled, generator.__name__, solver, metric.__name__, 
                                            dist_type, name_type, rep, 
                                            elapsed, n_iterations, reported_fx, final_fx)
                            print(csv_tuple, pheno)
                            rows.append(csv_tuple)
    columns = "Problem,Max depth,Macros,Generator,Solver,Metric,Dist type,Name type,rep,Elapsed,Iterations,Fitness,Test Fitness" 
    columns = columns.split(',')
    df = pd.DataFrame(rows, columns=columns)
    return df




def run_fdc():
    print('running FDC experiment')
    from pto.core.base import Op, Dist, tracer

    ##### sample many terms using generator
    ##### define a fitness function using test cases for ALL
    ##### run every term through the fitness function
    ##### run every term through shd versus the correct ALL

    global MACROS_ENABLED, MAX_DEPTH
    MACROS_ENABLED = lc.MACROS_ENABLED = lc_pto.MACROS_ENABLED = False
    MAX_DEPTH = lc.MAX_DEPTH = lc_pto.MAX_DEPTH = 12

    print(f'{MACROS_ENABLED=} {MAX_DEPTH=} {MACROS=} ')

    fitness_fn_discrete = (lambda expr: generic_fitness(expr, truth_tables['PLUS'], apply_binop, metric=discrete_metric))
    fitness_fn_shd = (lambda expr: generic_fitness(expr, truth_tables['PLUS'], apply_binop, metric=shd))

    op = Op(debruijn_generator, fitness_fn_discrete)

    known_sol = ALL
    n_reps = 5000
    rows = []
    start = time.time()
    for i in range(n_reps):
        sol = op.create_ind()
        expr, geno = sol
        # expr = debruijn_generator()
        d_phenotype = shd(known_sol, expr)
        fx_discrete = fitness_fn_discrete(expr)
        fx_shd = fitness_fn_shd(expr)
        rows.append((fx_discrete, fx_shd, d_phenotype))
        if i % 1000 == 0:
            current = time.time()
            elapsed = current - start   
            print(f'{elapsed:.2f}s: {i}/{n_reps}')
    df = pd.DataFrame(rows, columns=['fx_discrete', 'fx_shd', 'd_phenotype'])
    print(df)
    df.to_csv('fdc_distances.csv', index=False)
    # print correlations
    print(df.corr())





def run_probabilities():
    

    xs = {
        'NOT': NOT,
        'AND': AND, 
        # 'OR': OR,
        'SUCC': SUCC,
        'PLUS': PLUS,
        'IS_ZERO': IS_ZERO,
        'ALL': ALL,
        'FOLD': FOLD,
        'LENGTH': LENGTH
    }



    for k in xs:
        MACROS_ENABLED = lc.MACROS_ENABLED = lc_pto.MACROS_ENABLED = True
        MAX_DEPTH = lc.MAX_DEPTH = lc_pto.MAX_DEPTH = problems[k][0]
        
        print(k)
        x = xs[k]
        print('with macros')
        print(x)
        print(probability(x))
        print('with macros and new normalisation')
        xn = normalize_lambda_expression(x)
        print(xn)
        print(probability(xn))
        MACROS_ENABLED = lc.MACROS_ENABLED = lc_pto.MACROS_ENABLED = False
        print('without macros and not expanded')
        print(x)
        print(probability(x))
        print('without macros and expanded')
        xx = expand_macros(x)
        print(xx)
        print(probability(xx))
        print('without macros and expanded and alpha_converted')
        xxc = alpha_convert(expand_macros(x), base='x')
        print(xxc)
        print(probability(xxc))
        print('without macros and with new normalisation')
        xxn = normalize_lambda_expression(expand_macros(x), macros=macro_env)
        print(xxn)
        print(probability(xxn))
        print('---'*20)    


def init_worker():
    """Initialize each worker process"""
    print(f"Worker {os.getpid()} initializing...")
    
    # 1. Re-import everything to ensure fresh module state

    # # Try to completely reinitialize PTO
    # import sys
    
    # # Remove PTO modules from cache and reimport
    # pto_modules = [name for name in sys.modules.keys() if name.startswith('pto')]
    # for module_name in pto_modules:
    #     if module_name in sys.modules:
    #         del sys.modules[module_name]
    
    # Fresh import
    import pto
    from pto import run


    import lc
    import lc_pto
    from lc_functions import macro_env
    
    # 2. Reset global variables that are used across modules
    lc.MAX_DEPTH = 10  # Default value
    lc.MACROS_ENABLED = True  # Default value
    lc_pto.MAX_DEPTH = 10
    lc_pto.MACROS_ENABLED = True
    
    # 3. Ensure macro environment is properly set
    lc.macro_env = macro_env
    if hasattr(lc_pto, 'macro_env'):
        lc_pto.macro_env = macro_env
    
    # 4. Reset any PTO-specific state (this is the most likely culprit)
    try:
        import pto
        print(f"Worker {os.getpid()}: PTO rnd module: {pto.rnd}")
        print(f"Worker {os.getpid()}: PTO rnd type: {type(pto.rnd)}")
        print(f"Worker {os.getpid()}: PTO rnd dir: {[attr for attr in dir(pto.rnd) if not attr.startswith('_')]}")
        
        # Check if rnd has any state attributes
        if hasattr(pto.rnd, '__dict__'):
            print(f"Worker {os.getpid()}: PTO rnd state: {pto.rnd.__dict__}")
        
        # Try to reset or reinitialize the rnd object
        if hasattr(pto, 'reset_rnd'):
            pto.reset_rnd()
            print(f"Worker {os.getpid()}: Reset PTO rnd")
        elif hasattr(pto.rnd, 'reset'):
            pto.rnd.reset()
            print(f"Worker {os.getpid()}: Reset PTO rnd object")
        
    except Exception as e:
        print(f"Worker {os.getpid()}: Error debugging PTO state: {e}")
    
    # 5. Test that basic functionality works
    try:
        from lc_pto import debruijn_generator
        test_expr = debruijn_generator()
        print(f"Worker {os.getpid()}: Successfully generated test expression: {type(test_expr)}")
    except Exception as e:
        print(f"Worker {os.getpid()}: Error generating test expression: {e}")
    
    # 6. Test fitness function
    try:
        from lc_pto import list_fitness, truth_tables
        from lc import shd
        if test_expr:
            test_fitness = list_fitness(test_expr, truth_tables['ALL'], metric=shd)
            print(f"Worker {os.getpid()}: Test fitness: {test_fitness}")
    except Exception as e:
        print(f"Worker {os.getpid()}: Error computing test fitness: {e}")
    
    print(f"Worker {os.getpid()} initialization complete")


def run_experiment():
    n_reps_min, n_reps_max = 18, 19
    datestamp = datetime.now().strftime('%Y_%m_%_%H_%M_%S')   
    os.makedirs('outputs', exist_ok=True)
    os.makedirs('outputs/histories', exist_ok=True)
    os.makedirs('outputs/phenotypes', exist_ok=True)
    with Pool(processes=4) as pool:
        results_dfs = pool.map(run_one_rep, range(n_reps_min, n_reps_max))
        combined_df = pd.concat(results_dfs, ignore_index=True)

    combined_df.to_csv(f'outputs/results_lc_complete_18_{datestamp}.csv')



# def run_one_rep_simplified(rep):
#     stdlib_seed(rep)
    
#     # Match run_one_run exactly
#     global MACROS_ENABLED
#     MACROS_ENABLED = lc.MACROS_ENABLED = lc_pto.MACROS_ENABLED = False
#     lc.MAX_DEPTH = lc_pto.MAX_DEPTH = 12
    
#     start = time.time()
#     (pheno, geno), fx, history = run(
#         debruijn_generator, 
#         (lambda expr: list_fitness(expr, truth_tables['ALL'], metric=shd)),
#         better=min, 
#         Solver="hill_climber",
#         solver_args={'n_generation': 1000, 'return_history': True},
#         name_type='lin',
#         callback=terminate_on_success_callback)
#     end = time.time()
    
#     print(f"Rep {rep}: fx={fx}")
#     return fx



def run_one_run():

    global MACROS_ENABLED, MAX_DEPTH
    MACROS_ENABLED = lc.MACROS_ENABLED = lc_pto.MACROS_ENABLED = False
    MAX_DEPTH = lc.MAX_DEPTH = lc_pto.MAX_DEPTH = 12

    def ui_callback(state):
        try: # population-based
            (population, fitness_population, gen) = state
            best_fit = min(fitness_population)
            print_every = 10
        except: # single-point
            (individual, best_fit, gen) = state
            print_every = 1000
        if gen % print_every == 0:
            print(f'{datetime.now()} {gen} {best_fit}')
        return terminate_on_success_callback(state)

    print(f'{MACROS_ENABLED=} {MAX_DEPTH=} {MACROS=} ')
    Solver = "simulated_annealing" # "hill_climber" # "genetic_algorithm" # "hill_climber" # "random_search" # 
    solver_args = {'n_generation': 1000000, 'verbose': False}
    start = time.time()
    (pheno, geno), fx, num_gen = run(
                        debruijn_generator, 
                        (lambda expr: generic_fitness(expr, truth_tables['ALL'], apply_unary, metric=shd)),
                        better=min, 
                        Solver=Solver,
                        solver_args=solver_args,
                        name_type='str',
                        callback=ui_callback)
    end = time.time()
    elapsed = end - start   
    test_fn = (lambda expr: generic_fitness(expr, truth_tables['ALL_TEST'], apply_unary, metric=discrete_metric))
    final_fx = test_fn(pheno)
    print(elapsed, fx, final_fx, num_gen, pheno)
    print(geno)

def run_generator():
    n = 0
    for i in range(10000):
        x = debruijn_generator()
        if x is None:
            n += 1
            print(f'None has occurred {n} times')



def run_tests():
    def and_fitness(expr):
        return binop_fitness(expr, truth_tables['AND'], metric=shd)
    def not_fitness(expr):
        return unary_fitness(expr, truth_tables['NOT'], metric=shd)
    def all_fitness(expr):
        return list_fitness(expr, truth_tables['ALL'], metric=shd)
    def succ_fitness(expr):
        return unary_fitness(expr, SUCC_TRAINING_CASES, metric=shd)
    def is_zero_fitness(expr):
        return unary_fitness(expr, IS_ZERO_TRAINING_CASES, metric=shd)
    def plus_fitness(expr):
        return binop_fitness(expr, PLUS_TRAINING_CASES, metric=shd)
    
    lc_pto.MACROS_ENABLED = lc.MACROS_ENABLED = MACROS_ENABLED = False
    for fitness in (all_fitness, ): 
        (pheno, geno), fx, num_gen = run(debruijn_generator, fitness, better=min, solver_args={'n_generation': 1000},
                                        callback=terminate_on_success_callback, Solver='hill_climber', name_type="str")
        # print(f'Genotype {geno}')
        print(f'Solution {pheno}')
        print(f'Fitness {fx}')
        print(f'num_gen {num_gen}')
        # print(f'Post-run using all fitness {not_fitness(pheno)}')
        # print(f'Train fitness {unary_fitness(pheno, truth_tables["NOT"])}')
        # print(f'Test fitness {unary_fitness(pheno, truth_tables["NOT"])}')    
        # print(f'Post-run using SUCC fitness {succ_fitness(pheno)}')
        # print(f'Train fitness {unary_fitness(pheno, SUCC_TRAINING_CASES)}')
        # print(f'Test fitness {unary_fitness(pheno, SUCC_TEST_CASES)}')  

        # print(f'Post-run using IS_ZERO fitness {is_zero_fitness(pheno)}')
        # print(f'Train fitness {unary_fitness(pheno, IS_ZERO_TRAINING_CASES)}')
        # print(f'Test fitness {unary_fitness(pheno, IS_ZERO_TEST_CASES)}')  

        # print(f'Post-run using PLUS fitness {plus_fitness(pheno)}')
        # print(f'Train fitness {binop_fitness(pheno, PLUS_TRAINING_CASES)}')
        # print(f'Test fitness {binop_fitness(pheno, PLUS_TEST_CASES)}')  

        print(f'Post-run using all fitness {all_fitness(pheno)}')
        print(f'Train fitness {list_fitness(pheno, truth_tables["ALL"])}')
        print(f'Test fitness {list_fitness(pheno, truth_tables["ALL_TEST"])}')    

def run_several_runs_adhoc():
    print('ALL - debruijn, lin, 5k evals')
    print("rep, elapsed, fx, final_fx, num_gen, pheno")
    for i in range(20):
        stdlib_seed(i)
        print(i, end=' ')
        run_one_run()


def main():
    if len(sys.argv) != 2:
        print("Usage: python lc_experiments.py <rep_number>")
        sys.exit(1)
    
    rep = int(sys.argv[1])

    datestamp = datetime.now().strftime('%Y_%m_%_%H_%M_%S')   
    os.makedirs('outputs', exist_ok=True)
    os.makedirs('outputs/histories', exist_ok=True)
    os.makedirs('outputs/phenotypes', exist_ok=True)
    
    # Run single rep and save to individual file
    df = run_one_rep(rep)
    
    # Save individual result
    df.to_csv(f'outputs/rep_{rep}.csv', index=False)
    print(f"Completed rep {rep}")



# import json
# import multiprocessing as mp
# import os
# import sys
# from pprint import pformat

def capture_global_state():
    """Capture comprehensive global state information"""
    state = {}
    
    # Environment variables
    state['env_vars'] = dict(os.environ)
    
    # System path
    state['sys_path'] = sys.path.copy()
    
    # Loaded modules
    state['loaded_modules'] = list(sys.modules.keys())
    
    # Current working directory
    state['cwd'] = os.getcwd()
    
    # Process info
    state['process_id'] = os.getpid()
    state['parent_process_id'] = os.getppid()
    
    # Python version and executable
    state['python_version'] = sys.version
    state['python_executable'] = sys.executable
    
    # Random state (if numpy is loaded)
    # try:
    #     import numpy as np
    #     state['numpy_random_state'] = np.random.get_state()
    # except ImportError:
    #     pass
    
    # Standard random state
    import random
    # state['random_state'] = random.getstate()
    
    # Thread info
    import threading
    state['active_threads'] = [t.name for t in threading.enumerate()]
    
    # Global variables from your main module
    main_module = sys.modules.get('__main__')
    if main_module:
        main_globals = {k: type(v).__name__ for k, v in main_module.__dict__.items() 
                       if not k.startswith('_')}
        state['main_globals'] = main_globals
    
    return state

def save_state_to_file(state, filename):
    """Save state to a JSON file for diffing"""
    # Convert non-serializable objects to strings
    serializable_state = {}
    for key, value in state.items():
        try:
            json.dumps(value)
            serializable_state[key] = value
        except TypeError:
            serializable_state[key] = str(value)
    
    with open(filename, 'w') as f:
        json.dump(serializable_state, f, indent=2, sort_keys=True)


def worker_function(args):
    """Wrapper for multiprocessing"""
    # Capture state at start of worker
    state = capture_global_state()
    save_state_to_file(state, f'worker_state_{os.getpid()}.json')
    
    result = run_one_rep(0)
    return result

def state_debug():
    # Single process execution
    print("=== Single Process ===")
    state_single = capture_global_state()
    save_state_to_file(state_single, 'single_process_state.json')
    result_single = run_one_rep(0)
    print(f"Single process result: {result_single}")
    
    # Multiprocessing execution
    print("\n=== Multiprocessing ===")
    with mp.Pool(processes=1) as pool:
        result_multi = pool.map(worker_function, [None])[0]
    print(f"Multiprocessing result: {result_multi}")
    
    print("\nFiles generated:")
    print("- single_process_state.json")
    print("- worker_state_*.json")
    print("\nTo compare:")
    print("diff single_process_state.json worker_state_*.json")


def test_shd():
    expr1 = ONE
    expr2 = TWO
    print(f"SHD between {expr1} and {expr2}: {shd(expr1, expr2)}")

if __name__ == "__main__":

    #run_probabilities()
    run_experiment()
    # run_one_run()
    # run_generator()
    # run_tests()
    # run_several_runs_adhoc()
    # print(run_one_rep(0))
    # main()

    # state_debug()
    #run_fdc()
    # test_shd()