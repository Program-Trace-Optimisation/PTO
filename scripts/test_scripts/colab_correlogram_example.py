"""
Colab-ready example for correlogram analysis.

Instructions for Google Colab:
1. Upload this file to your Colab session or clone the PTO repository
2. Run this script
3. The correlogram will be generated and plotted

This works correctly in Colab because the generator function is defined
in a .py file (stable source location), not in a Colab cell.
"""

from pto import run, rnd
from pto.solvers.correlogram_walks import correlogram_walks

# Define problem in this file (not in Colab cell!)
def generator(size):
    """Generate random binary string"""
    return [rnd.choice([0, 1]) for i in range(size)]

def fitness(solution):
    """Count number of ones (ONEMAX)"""
    return sum(solution)

# Main execution
if __name__ == "__main__":
    print("="*60)
    print("Correlogram Analysis for ONEMAX (Colab-Compatible)")
    print("="*60)

    # Configuration
    PROBLEM_SIZE = 50
    N_WALKS = 40
    WALK_LENGTH = 15
    N_BINS = 20

    print(f"\nConfiguration:")
    print(f"  Problem size: {PROBLEM_SIZE}")
    print(f"  Random walks: {N_WALKS}")
    print(f"  Walk length: {WALK_LENGTH}")
    print(f"  Distance bins: {N_BINS}")

    # Create Op instance
    print("\nCreating Op instance...")
    op = run(
        generator,
        fitness,
        gen_args=(PROBLEM_SIZE,),
        better=max,
        Solver="search_operators"
    )

    # Build correlogram
    print("\nBuilding correlogram...")
    analyzer = correlogram_walks(
        op,
        n_walks=N_WALKS,
        walk_length=WALK_LENGTH,
        n_bins=N_BINS,
        verbose=True
    )

    x_axis, y_axis = analyzer()

    # Display results
    results = analyzer.get_results()

    print("\n" + "="*60)
    print("RESULTS")
    print("="*60)
    print(f"Solutions sampled: {results['n_solutions']}")
    print(f"Pairs analyzed: {results['n_pairs']}")
    print(f"Average distance: {results['avg_distance']:.2f}")
    print(f"Distance range: [{results['min_distance']:.0f}, {results['max_distance']:.0f}]")
    print(f"Fitness: {results['mean_fitness']:.2f} ± {results['std_fitness']:.2f}")
    print(f"Filled bins: {len(y_axis)}/{N_BINS}")

    if len(y_axis) > 0:
        print(f"\nCorrelation at d=0: {y_axis[0]:.4f}")

        # Interpret landscape
        if y_axis[0] > 0.8:
            print("  → Very smooth landscape at short distances")
        elif y_axis[0] > 0.5:
            print("  → Moderately smooth landscape")
        else:
            print("  → Rugged landscape")

    # Plot
    print("\nPlotting correlogram...")
    analyzer.plot(title=f"ONEMAX (size={PROBLEM_SIZE}) Fitness-Distance Correlogram")

    print("\n" + "="*60)
    print("Complete!")
    print("="*60)
