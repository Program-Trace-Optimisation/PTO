# CLAUDE.md - PTO Codebase Knowledge Base

## Project Overview

**PTO (Program Trace Optimisation)** is a universal metaheuristic optimization framework that achieves strict separation between problem definition and search algorithms. Users write generator functions using traced random operations, and PTO automatically extracts problem structure and designs appropriate search operators.

**Key Innovation:** Trace-based representation - records sequences of random decisions rather than encoding solutions directly.

## Quick Start

```python
from pto import run, rnd

def generator():
    return [rnd.choice([0, 1]) for i in range(10)]

(pheno, geno), fx = run(generator, sum, better=max)
```

## Architecture Overview

### Layered Design (4 Nested Levels)

```
User API (pto/__init__.py)
    ↓
Automatic Names Layer (pto/core/automatic_names/)
    ↓
Fine Distributions Layer (pto/core/fine_distributions/)
    ↓
Base Layer (pto/core/base/)
```

Each layer can be used independently for different complexity levels. Higher layers add features while maintaining compatibility.

## Directory Structure

```
PTO/
├── pto/                          # Main package
│   ├── __init__.py              # Exports run() and rnd
│   ├── core/                    # 3-layer optimization engine
│   │   ├── base/               # Tracer, distributions, operators (534 LOC)
│   │   ├── fine_distributions/ # Smart repair mechanisms (597 LOC)
│   │   └── automatic_names/    # AST-based naming (862 LOC)
│   ├── solvers/                # 6 search algorithms (832 LOC)
│   ├── problems/               # 11 example problems (1,187 LOC)
│   └── gui/                    # Jupyter widget interface (80+ LOC)
├── tests/                       # Unit test suite
├── docs/                        # Documentation
├── example.ipynb               # Interactive examples
└── README.md, DEVELOPERS.md    # Documentation
```

## Core Components

### 1. Base Layer (`pto/core/base/`)

**Purpose:** Foundation for trace-based optimization

**Key Files:**
- `tracer.py` (89 lines) - Records and replays stochastic operations
- `distribution.py` (72 lines) - Base `Dist` class for modeling distributions
- `trace_operators.py` (240 lines) - `Op` class with mutation/crossover operators
- `run.py` (82 lines) - Core run function coordinating optimization
- `check_immutable.py` (51 lines) - Validation decorator

**Key Classes:**
- `Tracer`: Context manager that activates/deactivates tracing
- `Dist`: Base distribution class with mutation/crossover interface
- `Op`: Operator class binding generator, fitness, and tracer
- `Sol`: Named tuple `(pheno, geno)` separating phenotype from genotype

**Control Flow:**
```
run() → Create Op instance → Solver calls Op methods:
  - create_ind(): generate new solution
  - evaluate_ind(): compute fitness
  - mutate_ind(): apply mutation
  - crossover_ind(): combine parents
```

### 2. Fine Distributions Layer (`pto/core/fine_distributions/`)

**Purpose:** Problem-aware repair and fine-grained mutations

**Key Files:**
- `distributions.py` (327 lines) - Specialized distribution classes
- `traceables.py` (66 lines) - `RandomTraceable` wrapper
- `supp.py` (195 lines) - RNG specifications and utilities

**Distribution Types:**
- `Random_real`: Continuous values with Gaussian mutation and bounds
- `Random_int`: Integer values with ±step mutations
- `Random_cat`: Categorical sampling with distribution-aware operators
- `Random_seq`: Sequence length mutations

**Key Feature:** Intelligent repair - when mutations hit invalid values, uses domain knowledge to find nearest valid alternative instead of re-sampling.

### 3. Automatic Names Layer (`pto/core/automatic_names/`)

**Purpose:** Structured naming from AST analysis for program-flow-aware operators

**Key Files:**
- `autogens.py` (82 lines) - `AutoNamedRandomTraceable` for automatic naming
- `annotators.py` (194 lines) - Name generation from program flow
- `autoplay.py` (39 lines) - `AutoPlayTracer` for tracing with names
- `node.py` (48 lines) - `Node` class tracking code location
- `ast_trans.py` (139 lines) - AST transformation utilities
- `gen.py` (120 lines) - Generator support functions
- `trans_run.py` (119 lines) - Top-level user-facing run function

**Naming Schemes:**
- **Linear:** Sequential integers (0, 1, 2, ...)
- **Structural:** Location-aware strings `func_name@(line,idx):count`

**Key Feature:** Enables tree-based trace visualization and program-flow-aware crossover operators.

### 4. Solvers (`pto/solvers/`)

Search algorithms and landscape analysis tools that work with any problem:

| Solver | File | Lines | Description |
|--------|------|-------|-------------|
| Hill Climber | `hill_climber.py` | 81 | Simple local search (default) |
| Random Search | `random_search.py` | 11 | Pure random sampling |
| Genetic Algorithm | `genetic_algorithm.py` | 127 | Population-based EA with elitism |
| PSO | `particle_swarm_optimisation.py` | 168 | Particle swarm with 3 velocity components |
| Novelty Search | `novelty_search.py` | 304 | Behavior-driven exploration with archive |
| Correlogram | `correlogram.py` | 126 | Landscape analysis via random sampling |
| Correlogram Walks | `correlogram_walks.py` | 270 | Landscape analysis via random walks |

**Common Parameters:**
- `n_generation` / `n_iteration`: Number of search iterations
- `mutation`: Mutation operator selection
- `crossover`: Crossover operator selection
- `callback`: Function for monitoring progress
- `return_history`: Boolean to track optimization history

**Solver Selection in `run()`:**
```python
run(generator, fitness, Solver='hill_climber', ...)
```

### 5. Problems (`pto/problems/`)

Eleven diverse example problems demonstrating PTO's versatility:

| Problem | File | Representation | Description |
|---------|------|----------------|-------------|
| ONEMAX | `onemax.py` | Binary string | Maximize number of 1s |
| Sphere | `sphere.py` | Continuous vector | Minimize sum of squares |
| TSP | `tsp.py` | Permutation/sequence | Traveling Salesman |
| Hello World | `helloworld.py` | String | Minimal string matching |
| Symbolic Regression | `symbolic_regression.py` | Tree | Evolve mathematical expressions |
| Grammatical Evolution | `grammatical_evolution.py` | Grammar-guided | Context-free grammar evolution |
| Graph Evolution | `graph_evolution.py` | Graph | Evolve graph structures |
| Neural Network | `neural_network.py` | Weight vector | NN weight optimization |
| Assignment | `assignment.py` | Permutation | Quadratic assignment problem |
| k-TSP | `k_tsp.py` | Multiple tours | Multiple salesman variant |
| Problem Classes | `as_classes.py` | Framework | Class abstractions for experiments |

**Problem Structure:**
```python
def generator():
    # Use rnd.choice(), rnd.randint(), rnd.random(), etc.
    return solution

def fitness(solution):
    return score

(pheno, geno), fx = run(generator, fitness, better=max)
```

## Key Concepts

### Traces (Genotypes)

**Definition:** Dictionary recording random decisions during generation

**Structure:**
```python
trace = {
    location_key: Dist(function, args, value, ...),
    ...
}
```

**Location Keys:**
- Base layer: Integers (0, 1, 2, ...)
- Automatic names: Strings `func@(line,col):count`

**Why Traces?**
- Universal representation for any data structure
- Captures problem structure automatically
- Enables intelligent operator design

### Random Traceable (`rnd`)

**Purpose:** Wrapper around `random` module that records decisions

**Available Methods:**
- `rnd.choice(seq)` - Select from sequence
- `rnd.randint(a, b)` - Random integer in [a, b]
- `rnd.random()` - Random float in [0, 1)
- `rnd.uniform(a, b)` - Random float in [a, b]
- `rnd.gauss(mu, sigma)` - Gaussian distribution
- `rnd.shuffle(seq)` - Shuffle sequence in-place

**Usage:** Use `rnd` instead of `random` in generator functions.

### Operators

**Mutation Types:**
- `mutate_random_ind`: Re-sample random trace entries
- `mutate_coarse_ind`: Re-sample with distribution matching
- `mutate_fine_ind`: Use distribution-specific smart mutations

**Crossover Types:**
- `crossover_uniform`: Uniform crossover on trace entries
- `crossover_one_point`: Single-point crossover
- Custom crossovers in specialized layers

### Solutions (Phenotypes)

**Sol Named Tuple:**
```python
Sol = namedtuple('Sol', ['pheno', 'geno'])
```

- `pheno`: Observable solution (what generator returns)
- `geno`: Trace (genotype encoding random decisions)

## Common Workflows

### 1. Basic Optimization

```python
from pto import run, rnd

def generator():
    return [rnd.choice([0, 1]) for _ in range(100)]

(solution, trace), fitness = run(generator, sum, better=max)
```

### 2. Custom Solver with Parameters

```python
from pto import run, rnd

result = run(
    generator,
    fitness,
    Solver='genetic_algorithm',
    population_size=100,
    n_generation=50,
    truncation_rate=0.5,
    better=max
)
```

### 3. With History Tracking

```python
(sol, trace), fx, history = run(
    generator,
    fitness,
    return_history=True,
    better=max
)

# history = list of (fitness, generation) tuples
```

### 4. Novelty Search (Behavior-Driven)

```python
def behavior_distance(pheno1, pheno2):
    # Define behavioral similarity
    return distance

result = run(
    generator,
    fitness,
    Solver='novelty_search',
    behavior_distance=behavior_distance,
    archive_size=100,
    k_nearest=15
)
```

### 5. Fitness Landscape Analysis with Correlogram

```python
from pto import run
from pto.solvers.correlogram_walks import correlogram_walks

# Create Op instance
op = run(
    generator,
    fitness,
    better=max,
    Solver="search_operators"
)

# Build correlogram using random walks
analyzer = correlogram_walks(
    op,
    n_walks=40,
    walk_length=15,
    n_bins=20,
    verbose=True
)

# Run analysis
x_axis, y_axis = analyzer()

# Plot results
analyzer.plot()

# Get detailed results
results = analyzer.get_results()
print(f"Average distance: {results['avg_distance']:.4f}")
print(f"Correlation at d=0: {y_axis[0]:.4f}")
```

### 6. Using Lower-Level Layers

```python
# Use base layer directly
from pto.core.base.run import run

# Use fine distributions without automatic names
from pto.core.fine_distributions.run import run
```

### 7. Interactive GUI

```python
from pto.gui.optimization_gui import OptimizationGUI
gui = OptimizationGUI()
gui.display()
```

## Design Patterns

### Strategy Pattern
- Solvers are interchangeable strategies
- Mutation/crossover operators selectable at runtime

### Template Method
- `Dist` base class defines interface
- Subclasses override with specialized behavior

### Decorator Pattern
- `@check_immutable` validates immutability
- Function wrapping in autogens

### Composition
- `Op` class composes generator, fitness, tracer
- Solvers use composed `Op` instance

### Factory Pattern
- `run()` dynamically loads solver classes
- Solver instantiation with configurable parameters

## Testing

**Run Tests:**
```bash
make test          # Run all tests
python -m unittest # Alternative
```

**Test Files:**
- `tests/test_solvers.py` - Tests for all 6 solvers
- Each solver tested with simple ONEMAX problem

**Coverage:** Unit tests cover core functionality, solvers, and basic problem integration.

## Dependencies

**Production (Core):**
- Python standard library only (random, copy, inspect, ast, functools)

**Optional (Examples & GUI):**
- numpy - Numerical computing
- matplotlib - Visualization
- scipy - Scientific computing
- ipywidgets - Jupyter GUI
- graphviz - AST visualization
- networkx - Graph operations

## Performance Considerations

### Tracing Overhead
- Each `rnd` call creates trace entry
- Trade-off: Slight runtime cost for automatic operator design
- Negligible for most problems

### Memory Usage
- Traces are dictionaries (O(n) where n = random calls)
- History tracking multiplies by generations
- Use `return_history=False` for long runs

### Optimization Tips
1. Minimize `rnd` calls in generator (each creates trace entry)
2. Use batch operations when possible
3. Choose appropriate solver for problem type
4. Tune solver parameters (population size, mutation rate)

## Academic Background

**Publications:**
- EuroGP 2018 - Original PTO paper
- EvoCOP 2019 - Extended version
- ROAR-NET COST Action integration

**Research Applications:**
- Landscape analysis via correlogram
- Novelty search for exploration behavior
- Genotype-phenotype correlation studies
- Effective dimensionality estimation

## Extension Points

### Adding a New Solver

```python
from pto.core.base.trace_operators import Op

class MySolver(Op):
    def __init__(self, generator, fitness, **kwargs):
        super().__init__(generator, fitness)
        # Initialize parameters

    def __call__(self):
        # Implement search logic
        # Use: self.create_ind(), self.evaluate_ind()
        #      self.mutate_ind(), self.crossover_ind()
        return best_sol, best_fitness
```

### Adding a New Problem

```python
# In pto/problems/my_problem.py
from pto import run, rnd

def generator():
    # Use rnd for all random decisions
    return solution

def fitness(solution):
    return score

if __name__ == '__main__':
    result = run(generator, fitness, better=max)
    print(result)
```

### Adding a New Distribution

```python
from pto.core.base.distribution import Dist

class MyDist(Dist):
    def mutate(self, *args, **kwargs):
        # Custom mutation logic
        return mutated_value

    def crossover(self, other, *args, **kwargs):
        # Custom crossover logic
        return crossed_value
```

## Common Issues & Solutions

### Issue: "Generator must be deterministic"
**Solution:** All randomness must go through `rnd`, not standard `random` module.

### Issue: Slow performance
**Solution:** Check number of `rnd` calls - each creates trace entry. Batch operations when possible.

### Issue: Solutions not improving
**Solution:**
1. Verify fitness function is correct
2. Check `better=max` or `better=min` is appropriate
3. Try different solver or increase generations
4. Increase mutation rate or population size

### Issue: Import errors
**Solution:** Ensure in correct layer - `from pto import run, rnd` for standard usage.

### Issue: Structural naming inconsistent in Jupyter/Colab
**Problem:** `name_type="str"` produces different trace keys for each solution in Jupyter/Colab environments.

**Symptoms:**
- Distance between solutions is doubled (includes spurious structural differences)
- Different solutions have no common trace keys
- Crossover operators may not work correctly

**Root Cause:** AST-based structural naming relies on source code introspection (`inspect.getsource()`) which behaves unreliably in interactive environments.

**Solution:** Define generator functions in a separate `.py` file and import them:

```python
# In my_problem.py
from pto import rnd

def generator(size):
    return [rnd.choice([0, 1]) for i in range(size)]

def fitness(solution):
    return sum(solution)
```

```python
# In Colab cell
from pto import run
from my_problem import generator, fitness

op = run(generator, fitness, gen_args=(50,), better=max, Solver="search_operators")
```

**Why this works:** Functions defined in `.py` files have stable source code locations, while functions defined in Colab cells have dynamic context that changes between calls.

**Alternative:** Use `name_type="lin"` in Colab (but loses structural intelligence).

## File Reference Quick Guide

**Need to understand:**
- Tracing mechanism → [pto/core/base/tracer.py](pto/core/base/tracer.py)
- Operators → [pto/core/base/trace_operators.py](pto/core/base/trace_operators.py)
- Distributions → [pto/core/fine_distributions/distributions.py](pto/core/fine_distributions/distributions.py)
- Automatic naming → [pto/core/automatic_names/autogens.py](pto/core/automatic_names/autogens.py)
- Main API → [pto/__init__.py](pto/__init__.py)

**Want to see examples:**
- Simple example → [pto/problems/helloworld.py](pto/problems/helloworld.py)
- Classic problem → [pto/problems/onemax.py](pto/problems/onemax.py)
- Complex structure → [pto/problems/symbolic_regression.py](pto/problems/symbolic_regression.py)
- Multiple implementations → [pto/problems/tsp.py](pto/problems/tsp.py)

**Need to modify:**
- Add solver → [pto/solvers/](pto/solvers/)
- Add problem → [pto/problems/](pto/problems/)
- Core logic → [pto/core/](pto/core/)

## Summary

PTO is a sophisticated, well-architected metaheuristic framework that elegantly separates problem specification from search algorithms. Its trace-based representation automatically adapts to arbitrary data structures, eliminating the need for manual encoding. The layered design allows progressive adoption of advanced features while maintaining simplicity for basic use cases.

**Philosophy:** Write simple generators with `rnd`, let PTO handle the optimization machinery.

**Strength:** Universal representation works with any data structure - strings, vectors, trees, graphs, permutations, neural networks.

**Use Case:** Rapid prototyping of optimization problems without manual operator design.

---

*Last Updated: 2026-01-11*
*Generated by: Claude Code*
