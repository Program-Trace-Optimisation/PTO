# Research scripts

Experiment drivers, analysis notebooks and results for research projects that use PTO.
These are not part of the installable `pto` package; they use it like any other library.
Install PTO with the packages they need from the repo root first: `pip install -e ".[research]"`.

## Projects

| Folder | Topic | Venue |
|--------|-------|-------|
| [evostar2025_pso/](evostar2025_pso/) | PSO and other solvers across problems, naming and distribution types; sequence-problem generators (`experiments_seq.py`) | EvoStar 2025 |
| [landscape_correlogram/](landscape_correlogram/) | Fitness landscape analysis via correlograms / variograms (plus two small usage examples and an exploratory symbolic-regression notebook) | in progress |
| [lambda_calculus_gptp/](lambda_calculus_gptp/) | Evolving lambda calculus terms | GPTP (submission) |

## Conventions

Each project is a self-contained folder:

```
scripts/<project>/
├── experiments*.py     # run the experiments, write to outputs/
├── analysis*.ipynb     # read outputs/, make figures and tables
└── outputs/            # results committed; large generated files git-ignored
```

- **Run everything from inside the project folder** (`cd scripts/<project>`); all paths
  are relative to it, e.g. `outputs/results_....csv`.
- **Naming:** `venueYEAR_topic` once a project targets a venue, plain `topic` while in progress.
- **New project:** create a new folder following the layout above, and add a row to the table.
- Reusable problem definitions belong in `pto/problems/`, not here.
- Per-run histories (`outputs/history_*`, `outputs/histories/`) and other bulky outputs are
  git-ignored; see the `scripts/` section of the repo's `.gitignore`.
- When a paper is submitted, consider tagging the commit (e.g. `git tag evostar2025`) so the
  results can be reproduced against the PTO version that produced them.

## Project-specific notes

- **lambda_calculus_gptp:** the problem code (`lc.py`, `lc_pto.py`) lives in
  `pto/problems/LambdaCalculus/`; `lc_experiments.py` adds that folder to `sys.path`.
  `python lc_experiments.py` runs `run_experiment()`; other entry points are commented
  out in its `__main__` block.
- **landscape_correlogram:** most of the data the notebook reads (`Landscape_*` folders,
  `Histories/`) is git-ignored and must be copied into `outputs/` locally.
  Requires `scikit-gstat`.
