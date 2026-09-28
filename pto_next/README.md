# pto_next: an experimental new core

`pto_next` is a from-scratch reimplementation of the PTO core, written to try out a
cleaner architecture. It runs alongside the original core (`pto`), which it does not
change, and has the same user interface, so the two can be compared on the same
problems.

```python
from pto_next import run, rnd

def generator():
    return [rnd.choice([0, 1]) for i in range(10)]

(pheno, geno), fx, num_gen = run(generator, sum, better=max)
```

After pulling, reinstall the editable package once (`pip install -e ".[dev]"`) so that
`pto_next` can be imported from outside the repository folder.

Tests: `python -m unittest discover -s tests/pto_next -t .`

## What stays the same

* A generator is an ordinary program; `rnd` is a drop-in for the `random` module.
* The trace is the genotype, and trace operators are built from operators on single
  random decisions.
* Solvers only see the operators: the solvers of `pto.solvers` (and the landscape tools)
  are used unchanged, because a `SearchSpace` has the same methods as the old `Op`
  (`create_ind`, `mutate_ind`, `crossover_ind`, `distance_ind`, ...).
* The problems of `pto.problems` run as they are: a generator's `rnd` from the old core
  is replaced by this core's `rnd` (for helpers nested in the generator; a helper
  defined elsewhere in a module that imports the old `rnd` would not be traced).

## Design

One concept per module, each using only those before it:

```
pto_next/
  trace.py           the engine: a trace records random decisions (choices); playing the
                     generator on a trace turns it into a solution, reusing, repairing
                     or sampling each decision
  distributions/     the kinds of random decision, and rnd
    base.py            Distribution: its methods are the coarse behaviour
    real.py  integer.py  categorical.py  sequences.py
  naming.py          how each decision gets its address: linear, dynamic, static
  _rewrite.py        (the source rewriting behind dynamic and static naming)
  search_operators/  how whole solutions are varied and compared
    mutation.py  crossover.py  distance.py
  space.py           SearchSpace: a problem bound to a naming, fine or coarse variation,
                     a random number generator and the chosen search operators
  run.py             run(): build a search space and run a solver on it
  _compat.py         (running generators written for the original core's rnd)
```

* **A distribution is complete.** Each class is one kind of random decision: an
  immutable value (its class and parameters) that knows how to sample a value and how
  its values vary (`mutate`, `crossover`, `convex_crossover`, `distance`, `repair`).
  The methods of the base class `Distribution` are the generic, coarse behaviour
  (resample, pick a parent, 0 or 1); a subclass overrides what it can do better (the
  fine behaviour). Coarse or fine is a switch of the search space: it calls either the
  distribution's own methods or those of `Distribution`. The trace is the same.
* **The engine knows nothing else.** `play()` is given how to repair a decision and a
  namer for decisions made without a name. `Choice(dist, value)` records are immutable,
  so an unchanged decision reuses its recorded choice.
* **rnd holds no state.** Each rnd function makes a distribution and calls
  `decide(distribution, name)`: during a play the decision is recorded, outside a play it
  is sampled from `random`, so a generator also runs without PTO.
* **Search operators are plain functions** of the search space: they only use
  `space.play(trace)`, `space.search_rng` and the variation of single decisions
  (`space.mutate_choice`, `space.crossover_choices`, ...).
* **Two random streams**, derived by name from the seed. `decision_rng` is the
  generator's randomness: the decisions sampled or repaired while playing a trace, the
  only randomness traces record. `search_rng` is the search's: search operators and
  solvers draw their random numbers from it, and it is never recorded. So with the
  same seed the initial solutions are the same whatever the operators and solver, and
  runs are reproducible in any process. The global `random` module is left to the user:
  problem data, a noisy fitness, and `rnd` outside a play.
* **No global configuration**: two search spaces with different settings coexist, and
  nothing one run does affects another.

## Extending: new distributions and search operators

Both are added as a module of their package (by system designers: users write
generators). A package imports all its modules when `pto_next` is imported, and it is an
error for two modules to define the same name.

**A distribution module** has the distribution classes, the rnd functions that make them
(with the signature of their counterpart in `random`, if there is one, plus `name=None`),
and `RND`, the tuple of those functions. Eg `pto_next/distributions/subset.py`:

```python
from .base import Choice, Distribution, decide

class Subset(Distribution):
    """subset(items): each item is in or out with probability 1/2."""
    __slots__ = ()

    def sample(self, rng):
        return tuple(x for x in self.params[0] if rng.random() < 0.5)

    def mutate(self, value, rng):              # optional: fine behaviour
        x = rng.choice(self.params[0])
        keep = set(value) ^ {x}                # add or remove one item
        return Choice(self, tuple(i for i in self.params[0] if i in keep))

def subset(items, *, name=None):
    return decide(Subset(tuple(items)), name)

RND = (subset,)
```

makes `rnd.subset(["ann", "bob", "cy"])` available in every generator, with every naming
(the tested version, `tests/pto_next/example_distribution.py`, also handles an empty
list of items and has a fine crossover and distance).
Methods it does not override (here crossover, distance, repair) are coarse. A fine method
that gets a choice of another kind of distribution falls back on the coarse one:
`if not self.same_kind(other): return Distribution.crossover(self, value, other, rng)`.

**A search operator module** has the operators, functions `(space, *parents) ->
Solution` (or `(space, a, b) -> float` for a distance), and `OPS`, the tuple of them. Eg
`pto_next/search_operators/two_points.py`:

```python
def mutate_two_points_ind(space, sol):
    """Mutate two different random decisions."""
    trace = dict(sol.geno)
    for address in space.search_rng.sample(list(trace), min(2, len(trace))):
        trace[address] = space.mutate_choice(trace[address])
    return space.play(trace)

OPS = (mutate_two_points_ind,)
```

is then chosen by name: `SearchSpace(..., mutation="mutate_two_points_ind")`, or
`run(..., solver_args={"mutation": "mutate_two_points_ind"})`. Both examples are tested
in `tests/pto_next/test_extension.py`.

### Addresses

A structured address is a tuple of segments, one per scope, ending with the call:

```python
def generator():
    def helper():
        return rnd.choice([0, 1])
    return [helper() for i in range(3)]
```

gives `(('comp', (4, 30), 0), ('helper', (4, 12)), ('choice', (3, 15)))`, shown by
`format_address` as `comp@4.30:0/helper@4.12/choice@3.15`: iteration 0 of the
comprehension at line 4, column 30, the call to `helper` at (4, 12), the `choice` call at
(3, 15). Positions are in the generator's source (line 1 is its `def` line). Scopes are
function calls, loop iterations and comprehension iterations.

Dynamic and static naming rewrite the generator with the same transformer and produce
**identical addresses**; they differ only in how:

* **Dynamic** (default) keeps the current scope as the generator runs. It also names
  calls in helpers defined outside the generator, from the call stack.
* **Static** compiles each address into the generator's code, so nothing is computed at
  run time. It only sees `rnd` calls written in the generator and its nested functions,
  which must be called directly by name; anything else is a clear error that suggests
  dynamic naming.
* **Linear** needs no source rewriting, so it also works for lambdas and methods.

## Differences from `pto`

| | `pto` | `pto_next` |
|---|---|---|
| Choosing the naming | `name_type='str'/'lin'`, `naming='dynamic'/'static'` | `naming='dynamic'/'static'/'linear'` |
| Choosing the operators | `dist_type='fine'/'coarse'` | `operators='fine'/'coarse'` |
| Configuration | process-wide (`rnd.CONFIG`, `Op.tracer`) | per `SearchSpace` |
| Addresses | strings; dynamic and static differ | tuples, the same for dynamic and static |
| Coarse vs fine | changes the class of the trace entries | same traces, different operators |
| Replaying an unchanged call | builds a new entry | reuses the recorded (immutable) choice |
| Randomness | the global `random` module | two streams per search space: `decision_rng` (the generator's decisions) and `search_rng` (search operators and solvers); the global `random` is not used |
| `run()` returns | a tuple | a `Result` (`best`, `fitness`, `generations`, `history`) that unpacks like the tuple |
| Permutation mutation (`shuffle`) | a swap, or half the time nothing | always a swap |
| Distances of permutations and samples | counts | normalised to [0, 1], like the other decisions |
| `rnd.gauss` and `rnd.normalvariate` | different decisions | the same distribution |

With the same seed, `pto_next` gives different numbers from `pto` (different random
streams and operator details), so results can be compared statistically but not
exactly.

## Speed

Milliseconds per operation, best of 7 runs, one machine (the trace sizes of the tree
problems differ between runs, as the random streams differ):

| Problem (trace entries) | mutation: `pto` dynamic → `pto_next` dynamic | `pto` static → `pto_next` static |
|---|---|---|
| OneMax (300) | 4.33 → 0.95 | 3.26 → 0.77 |
| Sphere (100) | 1.94 → 0.24 | 1.44 → 0.22 |
| Deep trees (~270) | 7.89 → 1.50 | 3.76 → 1.10 |
| TSP (1) | 0.174 → 0.010 | 0.130 → 0.010 |

The gains come from computing each decision's parameters once (no argument copying),
reusing unchanged choices on replay, and building addresses as tuples.

## Not yet

* The Jupyter GUI and `pto.gui.trace_tree` expect the old string names.
* `space_dimension_ind` (used by `as_classes`) is not implemented.
* Lambdas inside a generator have no scope of their own, and a nested function called
  through another function (eg `map(helper, xs)`) gets the address of that call, so
  repeated calls there can collide (dynamic) or are rejected (static).
