# CLAUDE.md

PTO (Program Trace Optimisation) is a Python metaheuristic framework. Users write a *generator*
that builds a random solution using `rnd` (a traced drop-in for the `random` module); the
sequence of random decisions (the *trace*) is the genotype, and PTO derives mutation and
crossover operators from it. Any solver works on any problem.

Many users are students working in forks. See README.md (user guide) and DEVELOPERS.md
(internals) before larger changes.

## Commands

```bash
pip install -e ".[dev]"                          # editable install with all extras + test tools
python -m unittest discover -s tests -t .        # unit tests (= make test; no make on Windows)
make test-notebooks                              # execute every notebook under tests/
python -m pto.problems.onemax                    # run an example problem
```

Python >= 3.10. The core has no third-party dependencies; extras (pyproject.toml): `examples`,
`landscape`, `gui`, `all`, `research`, `dev`.

## User API (keep README.md in sync with this)

```python
from pto import run, rnd

def generator(n):
    return [rnd.choice([0, 1]) for i in range(n)]

(pheno, geno), fx, num_gen = run(generator, sum, gen_args=(10,), better=max,
                                 Solver="genetic_algorithm",
                                 solver_args={"n_generation": 50, "crossover": "crossover_uniform_ind"})
```

- `run()` returns **three** values: `(sol, fx, num_gen)`; with `solver_args={"return_history": True}`
  the third is the fitness history. `Solver="search_operators"` returns the `Op` object instead.
- Solver parameters (`n_generation`, `mutation`, `crossover`, `population_size`, ...) go in
  `solver_args`, never as keyword arguments of `run()`.
- Other `run()` arguments: `fit_args`, `callback` (receives `(sol, fx, gen)` from hill_climber /
  random_search, `(population, fitnesses, gen)` from population solvers; returning true stops),
  `seed`, and research-only `name_type` (`"str"` default / `"lin"`), `dist_type` (`"fine"` default /
  `"coarse"`) and `naming` (`"dynamic"` default / `"static"`: structured names computed at run time or
  compile time; static needs `name_type="str"` and rejects `rnd` calls in helpers outside the generator).
- `Solver` is a name from `pto/solvers/` or a class. A solver is created as
  `Solver(op, better=..., callback=..., **solver_args)` and called with no arguments; it uses
  `op.create_ind / evaluate_ind / mutate_ind / crossover_ind / distance_ind`.
- Solvers: `hill_climber` (default), `random_search`, `genetic_algorithm`,
  `particle_swarm_optimisation` (also accepts `n_iteration`), `novelty_search` (needs
  `solver_args={"behavior_distance": f}`, a distance between phenotypes); landscape
  analysis: `correlogram`, `correlogram_walks` (imported lazily; need the `landscape` extra).
- Generator rules: must be a `def` function (not a lambda or method), because its source is
  re-parsed. Helpers with `rnd` calls work best nested inside it. Globals and aliases like
  `from pto import rnd as random` work. Problem data is generated with plain `random`, not `rnd`.

## Layout

- `pto/core/` - layers, each with its own `run()`: `base` (Tracer, Dist, Op) ->
  `fine_distributions` (fine Random_* distributions with repair, `rnd`) -> `automatic_names`
  (dynamic trace names; its `rnd` is `from pto import rnd`). `compiled_names` is the static
  alternative that injects names by AST rewriting, using the same `rnd`. `interface.run` is
  `from pto import run` and selects one with `naming=`; `rewrite.py` is their shared source rewriting.
- `pto/solvers/`, `pto/problems/` (standalone examples; `as_classes.py` wraps them as classes
  for experiments), `pto/gui/` (Jupyter GUI, `trace_tree` Graphviz visualisation).
- `tests/` - unittest `.py` files plus test notebooks. `tests/pto/test_user_api.py` mirrors the
  README examples; `tests/pto/test_problems.py` smoke-tests every problem class.
- `scripts/<project>/` - research experiments, one folder per project; run them from inside
  their folder (paths like `outputs/...` are relative). Not part of the package.
- `pto-webapp/` (JavaScript port, browser playground) and `pto-scheme/` (Racket port) are
  separate experimental implementations. Web app: `cd pto-webapp && npm ci && npm test`;
  after changing `src/`, `npm run build` and commit `ui/pto-bundle.js` (CI fails if it is stale).

## Pitfalls

- `rnd` and `Op.tracer` are process-wide and reconfigured by each layer's `run()`. An `Op`
  built directly on a specific tracer should get it explicitly: `Op(..., tracer=tracer)`.
  Otherwise tests can depend on test order.
- Changing a solver's return value or a problem function's signature breaks `pto/problems`,
  `as_classes.py`, the test notebooks and the scripts in `scripts/`; grep for callers.
- Generators can't be run via `python -c` or `exec` (no source to parse); use a `.py` file.
- Many files use CRLF line endings (`core.autocrlf=true`). Edit in place without changing them;
  a bulk `sed -i` rewrites every line. Notebooks: edit cell sources, keep JSON formatting.
- Don't execute notebooks that `pip install` PTO from GitHub outside Colab: that replaces an
  editable install (`example.ipynb` guards this with a Colab check).
- A stale non-editable install shadows the clone outside the repo root. Check with
  `python -c "import pto; print(pto.__file__)"`.
