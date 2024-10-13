# PTO
Program Trace Optimisation is a system for 'universal metaheuristic optimization made easy'. This is achieved by strictly separating the problem from the search algorithm.
New problem definitions and new generic search algorithms ('solvers') can be added to PTO easily and independently, and any algorithm can be used on any problem. PTO automatically extracts knowledge from the problem specification and designs search operators for the problem. The operators designed by PTO for standard representations coincide with existing ones, but PTO automatically designs operators for arbitrary representations.

This repository contains code implementing PTO in Python. The library itself is in `pto`, with `tests` and `docs` (in progress).

# Installation

`$ pip install git+ssh://git@github.com:Program-Trace-Optimisation/PTO.git`

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

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Program-Trace-Optimisation/PTO/blob/main/example.ipynb)

## The generator function

As we can see, the generator makes calls to `rnd` methods in the course
of generating a candidate solution. `rnd`
provides the same methods as the Python `random` module, but *traces*
them so that we can use the collection of random decisions as a genotype.
Because `rnd` mimics the `random` module API, you can test and debug your generator
outside PTO, using `import random as rnd`, and then bring it into PTO by instead using
`from PTO import run, rnd`.

The generator can call sub-functions, but they have to defined as nested
functions inside the generator function. (There is another approach which relaxes this
rule. TODO: document that approach elsewhere.)

## Extra optional arguments

If you don't need to pass any extra arguments to the generator, fitness function, or solver, the above is all you need.

If you do need to pass extra arguments, you can do so like this:

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

Several more examples are available in pto/problems/*.py.



# Contributing to PTO

Some fun projects for students could include:

* Write new solvers
* Consider advanced situations, such as multiobjective problems, interactive problems, dynamic environments, etc (we have substantial code which could be used as starting-points)
* Create an experiment manager (we have some code which could be usable as a starting point)
* Experiments with metrics on traces (we have substantially-developed code and theory, to be published soon, but further research is possible - contact us)

The ROAR-NET COST Action has working groups relevant to the goals of PTO. PTO has been presented there. COST Action members are especially invited to contact us and join in development. A COST Action Short-Term Scientific Mission is available also.


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

