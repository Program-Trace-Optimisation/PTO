# PTO
Program Trace Optimisation is a system for 'universal metaheuristic optimization made easy'. This is achieved by strictly separating the problem from the search algorithm.
New problem definitions and new generic search algorithms ('solvers') can be added to PTO easily and independently, and any algorithm can be used on any problem. PTO automatically extracts knowledge from the problem specification and designs search operators for the problem. The operators designed by PTO for standard representations coincide with existing ones, but PTO automatically designs operators for arbitrary representations.

This repository contains code implementing PTO in Python. The library itself is in `pto`, with `tests` and `docs` (in progress); see [Working on PTO](#working-on-pto) for the full layout.

# Online demo

To use PTO in a Google Colab notebook, with some small examples, please click here: 
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Program-Trace-Optimisation/PTO/blob/main/example.ipynb)

To use PTO with a simple GUI in a Google Colab notebook, please click here:
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Program-Trace-Optimisation/PTO/blob/main/pto/gui/simple_gui.ipynb) 

# Installation

PTO requires Python 3.10 or later. The core library has no dependencies outside the standard library.

`$ pip install git+https://github.com/Program-Trace-Optimisation/PTO.git`

To work on PTO itself, or to run the examples and tests, clone the repository and install it in
editable mode, so that changes to the code take effect without reinstalling:

```
$ git clone https://github.com/Program-Trace-Optimisation/PTO.git
$ cd PTO
$ pip install -e ".[all]"
```

The optional extras are `examples` (numpy, for some example problems), `landscape` (correlogram
landscape analysis), `gui` (Jupyter GUI and trace trees; trace trees also need the
[Graphviz](https://graphviz.org/download/) binaries), `all` (all of these) and `dev` (all, plus coverage).
Use `pip install -e .` for the core only.

If you previously installed PTO without `-e` (eg with `pip install git+...`), run the editable install
above: it replaces the old copy. Until you do, Python outside the clone's folder keeps importing
the old installed version, not your clone. Check with `python -c "import pto; print(pto.__file__)"`.

We will create a project on PyPI soon.

# Using PTO

It's easy to use PTO by adding your own problem. You can use your existing objective function, and then:

* **Write a generator!** This is a fun exercise for experienced metaheuristics researchers, as it is a new way of seeing the search space. You don't have to define an encoding, a genotype-phenotype mapping or repair method, or a mutation or crossover operator.

## Typical Workflow

1. `from pto import run, rnd`
2. `def generator():` - use `rnd` to make random decisions inside generator
3. `def fitness(solution):` - a typical fitness function
4. `run(generator, fitness)` - this will run a solver and return the best solution (a `(phenotype, genotype)` pair), its fitness value, and the number of generations run.

## Minimal ONEMAX

Here's the ONEMAX problem on 10 variables in minimal PTO style:

```python
from pto import run, rnd
def generator(): return [rnd.choice([0, 1]) for i in range(10)]
(pheno, geno), fx, num_gen = run(generator, sum, better=max)
```

## The generator function

As we can see, the generator makes calls to `rnd` methods in the course
of generating a candidate solution. `rnd`
provides the same methods as the Python `random` module, but *traces*
them so that we can use the collection of random decisions as a genotype.
Because `rnd` mimics the `random` module API, we can test and debug our generator
outside PTO, using `import random as rnd`, and then bring it into PTO by instead using
`from pto import run, rnd`.

`rnd` supports the random functions of the `random` module: `random`, `uniform`, `triangular`,
`gauss` and the other continuous distributions, `randint`, `randrange`, `choice`, `choices`,
`sample` and `shuffle`.

PTO reads the generator's source code to give each random decision a name that reflects
where it happens in the program (which loop iteration, which function call). So:

* The generator must be an ordinary function defined with `def`, in a `.py` file or a notebook
  cell. Lambdas and methods of a class do not work.
* The generator can call helper functions. Helpers that make random decisions work best
  nested inside the generator function: helpers defined outside it also work, but their random
  decisions get less informative names.
* The generator can use global variables and modules as usual.

On Google Colab, these names have been seen to differ between solutions of the same generator
defined in a notebook cell. If that happens, define the generator in a `.py` file and import it.

## Different operators

Operators are chosen by name through `solver_args`, and are used by the solvers that support them.

* There are three mutation operators (used by `hill_climber` and `genetic_algorithm`):
  * Point mutation, which makes one change: `run(..., solver_args={'mutation': 'mutate_point_ind'})`
  * Position-wise mutation, which changes every locus with a certain low probability: `run(..., solver_args={'mutation': 'mutate_position_wise_ind'})` (the default)
  * Random mutation, which generates a completely new individual: `run(..., solver_args={'mutation': 'mutate_random_ind'})`
* Crossover operators (used by `genetic_algorithm`):
  * Uniform crossover, which takes each value uniformly from one parent or the other: `run(..., Solver='genetic_algorithm', solver_args={'crossover': 'crossover_uniform_ind'})`
  * One-point crossover, which takes the aligned trace entries up to a random point from one parent and the rest from the other: `crossover_one_point_ind` (the default). The notion of a "point" is most natural for base PTO's linear traces; with structured names, uniform crossover is an alternative worth trying.
  * Convex crossover (`convex_crossover_ind`) works in the same way as uniform crossover but on three parents. It is used internally by `particle_swarm_optimisation` and cannot be selected for the GA.

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

`(pheno, geno), fx, num_gen = run(generator, sum, better=max, Solver='genetic_algorithm')`

Note the uppercase `S` above. This reflects that the genetic algorithm in this case
is a class, and inside `run()` an instance of it will be created.

We can also pass in arguments to be passed to the `solver`, eg the number of iterations
(`n_generation`; `particle_swarm_optimisation` also accepts its older name `n_iteration`).
We can ask for a history of best fitness values to be returned also; in that case
the third return value is the history instead of the number of generations.

`(pheno, geno), fx, history = run(generator, sum, better=max, 
                                  solver_args={'n_generation': 25, 'return_history': True})`

We can also pass a callback to be called by the solver, eg:

`run(generator, fitness, callback=lambda x: print(f"Hello from Solver callback! {x}"))`

The callback receives the search state `(sol, fx, generation)`; if it returns a true value,
the solver stops early.

For reproducible runs, pass a seed: `run(generator, fitness, seed=42)`.

Several more examples are available in [pto/problems/*.py](pto/problems/).

## Writing your own solver

A solver is any class that `run()` can create as `Solver(op, better=..., callback=..., **solver_args)`
and then call with no arguments, returning `(sol, fx, num_gen)`. `op` provides the search
operators designed by PTO for the problem: `op.create_ind()`, `op.evaluate_ind(sol)`,
`op.mutate_ind(sol)`, `op.crossover_ind(sol1, sol2)` and `op.distance_ind(sol1, sol2)`.
A solver never needs to know what the solutions look like.

```python
from pto import run, rnd

class restart_hill_climber:
    def __init__(self, op, better=max, callback=None, n_generation=100, n_restarts=5):
        self.op, self.better = op, better
        self.n_generation, self.n_restarts = n_generation, n_restarts

    def __call__(self):
        best = None
        for _ in range(self.n_restarts):
            sol = self.op.create_ind()
            fx = self.op.evaluate_ind(sol)
            for _ in range(self.n_generation):
                child = self.op.mutate_ind(sol)
                fc = self.op.evaluate_ind(child)
                sol, fx = self.better([(sol, fx), (child, fc)], key=lambda s: s[1])
            best = (sol, fx) if best is None else self.better([best, (sol, fx)], key=lambda s: s[1])
        return best[0], best[1], self.n_restarts * self.n_generation

def generator(): return [rnd.choice([0, 1]) for i in range(10)]
(pheno, geno), fx, num_gen = run(generator, sum, better=max,
                                 Solver=restart_hill_climber, solver_args={'n_restarts': 3})
```

Pass the class itself as `Solver`, so it can live in your own file. To make it available by
name (`Solver='restart_hill_climber'`), put it in `pto/solvers/restart_hill_climber.py`, with
the class named like the file. See [pto/solvers/hill_climber.py](pto/solvers/hill_climber.py)
for a solver that also supports `callback`, `verbose` and `return_history`.

## Experimenting with the operators

`run(..., Solver='search_operators')` does not run a search: it returns the `op` object, so
you can study the operators on their own:

```python
op = run(generator, sum, better=max, Solver='search_operators')
parent = op.create_ind()
child = op.mutate_ind(parent)
print(parent.pheno, child.pheno, op.distance_ind(parent, child))
```



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


# Working on PTO

To work on your own copy, fork the repository on GitHub, clone your fork, and install it in
editable mode as described under [Installation](#installation).

Where things are:

* `pto/` - the library. `pto/problems/` has example problems, `pto/solvers/` the solvers,
  `pto/core/` the tracing machinery (see [DEVELOPERS.md](DEVELOPERS.md)).
* `tests/` - unit tests (`.py`) and test notebooks (`.ipynb`).
* `scripts/` - experiments for research projects, one folder per project (see
  [scripts/README.md](scripts/README.md)). Put a new project in its own folder there.
* `docs/` - figures used in documentation.
* `pto-webapp/` and `pto-scheme/` - experimental ports of PTO to JavaScript and Racket.

# Code style

If adding a solver, we recommend to use the argument names:

* `n_generation` for the number of iterations of the search algorithm
* `better`, `callback`, `verbose` and `return_history` with the same meaning as in
  [hill_climber.py](pto/solvers/hill_climber.py)

# Tests

Run the unit tests (from the repository root):

`$ make test`

or, without `make` (eg on Windows):

`$ python -m unittest discover -s tests -t .`

To also execute every test notebook (needs `pip install -e ".[dev]"`):

`$ make test-notebooks`

When you change the code, run the tests before and after. When you add a problem or a
solver, add a test for it under `tests/`, eg in
[tests/pto/test_problems.py](tests/pto/test_problems.py) or
[tests/pto/test_user_api.py](tests/pto/test_user_api.py).

Please help us by submitting bug reports! Thanks!



# Old version of PTO

A previous version of PTO was described in two papers, published at EuroGP 2018 and EvoCOP 2019. If you wish to access that version for reproducibility of those papers, please see [this repo](https://github.com/Program-Trace-Optimisation/PTO_EvoSTAR_2018_EvoCOP_2019).
