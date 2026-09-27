"""
Example usage of correlogram_walks for fitness landscape analysis.

This script demonstrates how to use the correlogram_walks analyzer
to study fitness-distance correlations through random walks.

Usage in Colab or Jupyter:
    # Simply import and run from the installed PTO package
    from pto import run
    from pto.solvers.correlogram_walks import correlogram_walks
    from pto.problems.onemax import generator, fitness

    # Create Op instance
    op = run(generator, fitness, gen_args=(50,), better=max, Solver="search_operators")

    # Build and plot correlogram
    analyzer = correlogram_walks(op, n_walks=40, walk_length=15, verbose=True)
    x, y = analyzer()
    analyzer.plot()
"""

from pto import run
from pto.solvers.correlogram_walks import correlogram_walks
from pto.problems.onemax import generator, fitness

print("="*60)
print("Correlogram Analysis Example: ONEMAX Problem")
print("="*60)

# Create Op instance
print("\nStep 1: Creating Op instance...")
op = run(
    generator,
    fitness,
    gen_args=(50,),  # Problem size
    better=max,
    Solver="search_operators"
)

print("Op instance created successfully!")
print(f"  Generator: ONEMAX (binary string optimization)")
print(f"  Problem size: 50")
print(f"  Naming: structural (name_type='str')")

# Create correlogram analyzer
print("\nStep 2: Creating correlogram analyzer...")
analyzer = correlogram_walks(
    op,
    n_walks=40,
    walk_length=15,
    n_bins=20,
    verbose=True
)

print("\nStep 3: Running analysis...")
x_axis, y_axis = analyzer()

# Get detailed results
results = analyzer.get_results()

print("\n" + "="*60)
print("RESULTS SUMMARY")
print("="*60)
print(f"Total solutions sampled: {results['n_solutions']}")
print(f"Total pairs analyzed: {results['n_pairs']}")
print(f"Average distance: {results['avg_distance']:.4f}")
print(f"Distance range: [{results['min_distance']:.4f}, {results['max_distance']:.4f}]")
print(f"Fitness mean ± std: {results['mean_fitness']:.2f} ± {results['std_fitness']:.2f}")
print(f"Non-empty bins: {len(results['bin_counts'])}/{results['n_bins']}")

if len(y_axis) > 0:
    print(f"\nCorrelation at distance=0: {y_axis[0]:.4f}")
    import numpy as np
    print(f"Correlation at avg distance: {np.interp(results['avg_distance'], x_axis, y_axis):.4f}")

# Plot the correlogram
print("\nStep 4: Plotting correlogram...")
analyzer.plot(title="ONEMAX Fitness-Distance Correlogram")

print("\n" + "="*60)
print("Analysis complete!")
print("="*60)
