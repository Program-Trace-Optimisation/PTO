import random
from .run import run as name_run
from .gen import gen_fun


def run(Gen, *args, seed=None, **kwargs):
    """
    Run a solver on a problem, as specified by a generator and fitness function.

    Parameters:

    * Gen: a PTO generator function, which internally calls methods on rnd
    * Fitness: a fitness function
    * Solver: a class representing a metaheuristic such as a GA
    * better: either min or max, indicating whether this objective is to be minimised or maximised
    * gen_args: optional tuple with arguments to be passed to the generator, when run() calls it
    * fit_args: optional tuple with arguments to be passed to the fitness function, when run() calls it
    * solver_args: optional dict with keyword args to be passed to the solver when run() instantiates it
    * callback: a function to be called during optimisation
    * seed: optional random seed for reproducibility
    * name_type: a string, can be
      * 'lin' (trace uses linear names) or
      * 'str' (structured names)
      For PTO research use only, not for use by end-users.
    * dist_type: a string, can be
      * 'coarse' (trace elements use coarse distributions) or
      * 'repair' (fine distributions with repair)
      For PTO research use only, not for use by end-users.

    Return: the best solution found and its fitness
    sol, fx: sol is a tuple (genotype, phenotype) and fx is a float.


    Here is the typical PTO workflow:

    1. `from pto import run, rnd`
    2. `def generator():` - use `rnd` to make random decisions inside generator
    3. `def fitness(solution):` - a typical fitness function
    4. `run(generator, fitness)` - this will run a solver and return a genotype, phenotype, and fitness value.

    Here's the ONEMAX problem on 10 variables in minimal PTO style:

    ```python
    from pto import run, rnd
    def generator(): return [rnd.choice([0, 1]) for i in range(10)]
    (pheno, geno), fx = run(generator, sum, better=max)
    ```

    As we can see, the generator makes calls to `rnd` methods. `rnd`
    provides the same methods as the Python `random` module, but *traces*
    them so that we can use the collection of random decisions as a genotype.
    Because `rnd` mimics the `random` module API, we can test and debug our generator
    outside PTO, using `import random as rnd`, and then bring it into PTO by instead using
    `from PTO import run, rnd`.

    The generator can call sub-functions, but they have to defined as nested
    functions inside the generator function. (There is another approach which relaxes this
    rule. TODO: document that approach elsewhere.)

    For basic usage the above is all we need.

    If we need to pass extra arguments to the generator, fitness function, or solver,
    we can do so like this:

    1. `from pto import run, rnd`
    2. `def generator(N):` - eg N might be a problem size
    3. `def fitness(x, dist):` - eg use a matrix of distances during fitness calculation
    4. Call `run(generator, fitness, gen_args=(N,), fit_args=(dist,),
                  solver_args={n_generation: 100}, better=min)`

    This allows `run()` to pass the problem data to `fitness` and `generator`,
    and passes an argument to set the number of iterations in the `solver`,
    and also specifies that this is a minimisation problem rather than maximisation,
    with `better=min`.

    We can also pass a callback to be called by the solver, eg:

    `run(generator, fitness, callback=lambda x: print(f"Hello from Solver callback! {x}"))`

    If we need to generate problem data, we use Python's `random` module as normal, not `rnd`.
    Similarly, if we want to control the random state of the solver, we use `random.seed()`, not `rnd`.

    Note: Numpy can be used in generating problem data, and in a solver algorithm, but cannot
    be used in a PTO generator. An extension of PTO will lift this restriction in future.

    Several more examples are available in pto/problems/*.py.

    """

    # Set random seed globally for the framework while preserving original state
    if seed is not None:
        rng_state = random.getstate()  # Save current state
        random.seed(seed)

    Gen = gen_fun(Gen)
    result = name_run(Gen, *args, **kwargs)

    # Restore random generator to previous state
    if seed is not None:
        random.setstate(rng_state)

    return result


# FEATURES/LIMITATIONS:
#
# 1) To affect naming, all functions called by the generator must be nested in the generator function definition (silent problem/error)
#
# 2) the generator cannot refer to global variables/names (error)
#
# 3) all primitive generators are magically available without import and must start with 'rnd.' (error)
#
# 4) generators cannot be defined as methods in classes (error)


# Gen = gen(Gen, level=2, skipline=False)
# frame level 2 as gen used in nested name scope (not where Gen was defined)
# a more robust solution could be using global in the name space in the dfinition of gen?
# skipline false becuase we should not remove first line of source as gen is not used with decorator syntax (@gen)
