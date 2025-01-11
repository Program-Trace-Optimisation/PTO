# PTO
Program Trace Optimisation is a system for 'universal metaheuristic optimization made easy'. This is achieved by strictly separating the problem from the search algorithm.
New problem definitions and new generic search algorithms ('solvers') can be added to PTO easily and independently, and any algorithm can be used on any problem. PTO automatically extracts knowledge from the problem specification and designs search operators for the problem. The operators designed by PTO for standard representations coincide with existing ones, but PTO automatically designs operators for arbitrary representations.

This repository contains code implementing PTO in Python. The library itself is in `pto`, with `tests` and `docs` (in progress).

# Online demo

To use PTO in a Google Colab notebook, with some small examples, please click here: 
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Program-Trace-Optimisation/PTO/blob/main/example.ipynb)

To use PTO with a simple GUI in a Google Colab notebook, please click here:
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Program-Trace-Optimisation/PTO/blob/main/pto/gui/simple_gui.ipynb) 

# Installation

`$ pip install git+https://git@github.com:Program-Trace-Optimisation/PTO.git`

Alternatively, after downloading the code (eg using `git clone`):

`$ pip install -e .`

We will create a project on PyPI soon.

# Using PTO

It's easy to use PTO by adding your own problem. You can use your existing objective function, and then:

* **Write a generator!** This is a fun exercise for experienced metaheuristics researchers, as it is a new way of seeing the search space. You don't have to define an encoding, a genotype-phenotype mapping or repair method, or a mutation or crossover operator.

## Typical Workflow

1. `from pto import run, rnd`
2. `def generator():` - use `rnd` to make random decisions inside generator
3. `def fitness(solution):` - a typical fitness function
4. `run(generator, fitness)` - this will run a solver and return a genotype, phenotype, and fitness value.

## Minimal ONEMAX

Here's the ONEMAX problem on 10 variables in minimal PTO style:

```python
from pto import run, rnd
def generator(): return [rnd.choice([0, 1]) for i in range(10)]
(pheno, geno), fx = run(generator, sum, better=max)
```

## The generator function

As we can see, the generator makes calls to `rnd` methods in the course
of generating a candidate solution. `rnd`
provides the same methods as the Python `random` module, but *traces*
them so that we can use the collection of random decisions as a genotype.
Because `rnd` mimics the `random` module API, we can test and debug our generator
outside PTO, using `import random as rnd`, and then bring it into PTO by instead using
`from PTO import run, rnd`.

The generator can call sub-functions, but they have to defined as nested
functions inside the generator function. (There is another approach which relaxes this
rule. TODO: document that approach elsewhere.)

## Different operators

* There are three mutation operators:
  * Point mutation, which makes one change: pass in `run(..., mutation='mutate_point_ind')`
  * Position-wise mutation, which changes every locus with a certain low probability: pass `run(..., mutation='mutate_position_wise_ind')`
  * Random mutation, which generates a completely new individual: pass in `run(..., mutation='mutate_random_ind')`
* There are two crossover operators:
  * Uniform crossover, which takes each value uniformly from one parent or the other: pass in `run(..., crossover='crossover_uniform_ind')`
  * Convex crossover, which operates in the same way but on three parents: pass in `run(..., crossover='crossover_convex_ind')`
  * (There is also one-point crossover, `crossover_one_point_ind`, which is well-defined only for base PTO, and so should not be used.)

## Extra optional arguments

For basic usage the above is all we need.

If we need to pass extra arguments to the generator, fitness function, or solver, 
we can do so like this:

1. `from pto import run, rnd`
2. `def generator(N):` - eg N might be a problem size
3. `def fitness(x, dist):` - eg use a matrix of distances during fitness calculation
4. Call `run(generator, fitness, gen_args=(N,), fit_args=(dist,), better=min)`
    
This allows `run()` to pass the problem data to `fitness` and `generator`, 
and also specifies that this is a minimisation problem rather than maximisation, 
with `better=min`.

If we need to generate problem data, eg training data, 
we use Python's `random` module as normal, not `rnd`.
Similarly, if we want to control the random state of the solver, 
we use `random.seed()`, not `rnd`.

Note: Numpy can be used in generating problem data, and in a solver algorithm, but cannot
be used in a PTO generator. An extension of PTO will lift this restriction in future. 


## Solver arguments

The default solver is a hill-climber, but we can chose any of the following by passing in a string: 
* `random_search`
* `hill_climber`
* `genetic_algorithm`
* `particle_swarm_optimisation`.

`(pheno, geno), fx = run(generator, sum, better=max, Solver='genetic_algorithm')`

Note the uppercase `S` above. This reflects that the genetic algorithm in this case
is a class, and inside `run()` an instance of it will be created.

We can also pass in arguments to be passed to the `solver`, eg the number of iterations.
We can ask for a history of best fitness values to be returned also.

`(pheno, geno), fx, history = run(generator, sum, better=max, 
                                  solver_args={'n_generation': 25, 'return_history': True})`

We can also pass a callback to be called by the solver, eg:

`run(generator, fitness, callback=lambda x: print(f"Hello from Solver callback! {x}"))`

Several more examples are available in [pto/problems/*.py](pto/problems/).



# Contributing to PTO

PTO is developed by Alberto Moraglio (albmor@gmail.com) and James McDermott (jamesmichaelmcdermott@gmail.com). We welcome contributions from the community.

See [here](DEVELOPERS.md) for more information on core concepts in the PTO implementation.

Some fun projects for students could include:

* Write new solvers.
* Consider advanced situations, such as multiobjective problems, interactive problems, dynamic environments, etc (we have substantial code which could be used as starting-points).
* Create an experiment manager (we have some code which could be usable as a starting point).
* Experiments with metrics on traces (we have substantially-developed code and theory, to be published soon, but further research is possible - contact us)
* Numpy extension for generators (contact us).

The [ROAR-NET COST Action](https://roar-net.eu/) has working groups relevant to the goals of PTO. PTO has been presented there. COST Action members are especially invited to contact us and join in development. A COST Action Short-Term Scientific Mission is available also.


# Code style

If adding a solver, we recommend to use the argument names:

* `n_generation` for the number of iterations of the search algorithm

(More to come here.)

# Tests

We have a proof-of-concept test suite. Run:

`$ make test`

It will discover unit tests under `tests/`

We have more tests in `.ipynb` files, which (TODO) we will gradually convert to automated unit tests.

Please help us by submitting bug reports! Thanks!



# Old version of PTO

A previous version of PTO was described in two papers, published at EuroGP 2018 and EvoCOP 2019. If you wish to access that version for reproducibility of those papers, please see [this repo](https://github.com/Program-Trace-Optimisation/PTO_EvoSTAR_2018_EvoCOP_2019). [A draft of the EuroGP 2018 appers](docs/paper_2018.pdf) is available.

