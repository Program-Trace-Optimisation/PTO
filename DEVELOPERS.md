# Core concepts

To understand the code as a developer, the following concepts are essential:

* There is `base` PTO, and then there are two extensions which are crucial for good optimisation behaviour:
  * `fine_distributions`, with `repair`
  * `automatic_names`.
* The core code is organised in layers partly reflecting those extensions. Each layer has its own `run()` and builds on the one below:
  * `pto/core/base/` - the `Tracer` (records and replays random decisions), the coarse distribution `Dist`, and the trace operators in `Op`. Names are given by hand, eg `tracer.sample('pos 1', Dist(random.random))`.
  * `pto/core/fine_distributions/` - the fine distributions `Random_real`, `Random_int`, `Random_cat`, `Random_seq`, with fine mutation, crossover and `repair`, and `rnd` (`RandomTraceable`), which wraps each `random` function listed in `supp.rng_specs`. Names are still given by hand: `rnd.random(name='pos 1')`.
  * `pto/core/automatic_names/` - automatic names. `rnd` here fills in `name=` automatically, either sequentially (`lin`) or structurally (`str`), using the call stack at run time. `trans_run.run` first rewrites the generator's AST (`gen.gen_fun`) so that nested functions and loops are annotated. This is the `run` and `rnd` exported by `from pto import run, rnd`.
  * `pto/core/compiled_names/` - an alternative to `automatic_names` with the same user interface: the generator's AST is rewritten once so that every `rnd.X(...)` call gets a `name=` argument, and then `fine_distributions` does the rest. `tests/pto/core/compiled_names/test_vs_automatic_names.py` checks that the two agree.
* The `run` method detailed in our README hides all of this complexity from users. There are multiple `run` methods for the multiple layers, but the user will only `from pto import run` which gives the user-facing version.
* The trace operators - initialisation, mutation, and combination operators which operate on traces (ie genotypes) and are used in PTO solvers - are implemented as compound operators, where the primitives are individual random decisions.
* Each individual random decision in a generator is made by some call to a PTO `rnd` method, which corresponds to a same-named method in the Python `random` module. `rnd.random()` gives a continuous variable with some distribution, `rnd.randrange` gives an ordinal variable, and `rnd.choice` gives a categorical variable. All other distributions can be composed out of these. For each of these, PTO models the distribution with a class which knows how to do initialisation, mutation, and combination. We call these distribution operators. In `base` PTO, initialisation is just sampling, and mutation is just re-sampling, which is a "coarse" change. Combination is just choosing the value from one or other parent. In both mutation and combination, it could happen that the offspring calls the same `rnd` method in the same trace location, but with different arguments. In that case, in `base` PTO, both mutation and combination just fall back to re-sampling, which is a "coarse" change.
* In `fine_distribution` both mutation and crossover are smarter, for continuous and ordinal variables, taking better advantage of what we know about the specific distribution to achieve a "fine" change. Also in `fine_distribution`, for continuous, ordinal, and categorical variables, smart `repair` methods try to re-use values from parents as much as possible when doing mutation and combination, even if the random call in the offspring has arguments which are not the same as the arguments in the parent.
* In PTO, traces are represented as `dict` objects. Each key represents a `rnd` call - analogous to a locus in a genotype, and each value represents the value stored there - analogous to an allele. In `base` PTO, traces are linear, that is they are organised as a sequence of random decisions, similar to PODI and Decision Chain Encoding. Therefore, the keys are just sequential integers. In PTO with `automatic_names` instead the keys are structured to represent the location of the `rnd` call in the execution trace of the generator in a structured way, that is the include the location in the generator's program flow (conditionals and loops and recursions). Thanks to the structure of program flow, we can then view the trace as a tree. For example, with

  ```python
  def generator():
      def helper():
          return rnd.choice([0, 1])
      return [helper() for _ in range(5)]
  ```

  the first random decision has the key `root/iter@(4,8):0/helper@(4,28)/choice@(3,54)`: iteration `0` of the comprehension on line 4, inside the call to `helper` on line 4, the `choice` call on line 3 (line numbers are within the generator; the second number is a position in the bytecode). Keys are split at `/` to form the tree; `pto.gui.trace_tree` draws it (examples in [docs/images/trace_trees/](docs/images/trace_trees/)). Two solutions share the keys of the decisions they have in common, and the operators align traces on those shared keys.
* The default in `run()` is to use the best-behaving operators, which means using: `run(..., name_type='str', dist_type='fine')`. The defaults can be over-ridden:
  * `name_type` can be `lin` or `str`
  * `dist_type` can be `coarse` or `fine`. The latter includes switching on `repair`.
  * However, the defaults **should not** be over-ridden by users or even by researcher. A typical experiment, eg comparing `lin` versus `str` performance, is not a sensible experiment unless the researcher knows what they're doing.
* The trace operators and distribution operators described above are provided by the `Op` class. So, solvers just use an instance of `Op`, eg `offspring = self.op.mutate_ind(individual)`. To create an instance we would need to pass in the generator and fitness function.
* If we want to do experiments with PTO other than just using `run`, to make it easy to set it up correctly, we have provided the special `Solver` option `run(generator, fitness, ..., Solver='search_operators')` which doesn't do a real run, it just sets up an instance of `Op`, which can be used eg for experiments studying the behaviour of the operators in isolation.


# Global state to be aware of

* `rnd` and the tracers are module-level objects shared by the whole process. Each layer's `run()` reconfigures them: `automatic_names.run` calls `rnd.CONFIG(name_type=..., dist_type=...)` and sets the class-level `Op.tracer`; `compiled_names.run` sets `Op.tracer` back to the base tracer. So one run can affect how later code in the same process is traced.
* An `Op` created without a `tracer` argument uses the class-level `Op.tracer`. Code that builds an `Op` directly on a particular tracer (eg the solver tests, which use the base tracer) should pass it explicitly: `Op(generator=gen, fitness=fit, tracer=tracer)`.
* `Tracer.play` deactivates the tracer even if the generator raises, so an error in one solution does not leave later untraced code being traced.

# Tests

See the Tests section of the [README](README.md#tests). `make test` runs the unit tests in `tests/`; `make test-notebooks` executes the notebooks in `tests/`.
