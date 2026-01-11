"""
Correlogram builder using random walks for fitness landscape analysis.

This module provides fitness-distance correlation analysis by generating
random walks through repeated mutations and analyzing the relationship
between genotypic distance and fitness correlation.
"""

import numpy as np
import matplotlib.pyplot as plt


class correlogram_walks:
    """
    Build a correlogram using random walks through the fitness landscape.

    This analyzer generates multiple random walks by repeatedly mutating solutions,
    then computes fitness-distance correlations to characterize landscape structure.

    Parameters:
        op: Operator instance with create_ind, mutate_ind, evaluate_ind, distance_ind
        n_walks (int): Number of random walks to perform (default: 50)
        walk_length (int): Number of mutations per walk (default: 20)
        n_bins (int): Number of distance bins for grouping (default: 20)
        verbose (bool): Whether to print progress messages (default: False)

    Example:
        >>> from pto import run
        >>> from pto.solvers.correlogram_walks import correlogram_walks
        >>>
        >>> op = run(generator, fitness, better=max, Solver="search_operators")
        >>> analyzer = correlogram_walks(op, n_walks=40, walk_length=15)
        >>> x_axis, y_axis = analyzer()
        >>> analyzer.plot()
    """

    def __init__(
        self,
        op,
        n_walks=50,
        walk_length=20,
        n_bins=20,
        verbose=False,
        **kwargs
    ):
        self.op = op
        self.n_walks = n_walks
        self.walk_length = walk_length
        self.n_bins = n_bins
        self.verbose = verbose

        # Results storage
        self.x_axis = None
        self.y_axis = None
        self.avg_distance = None
        self.results = None

    def __call__(self):
        """
        Execute the correlogram analysis.

        Returns:
            tuple: (x_axis, y_axis) where:
                - x_axis: List of distance bin centers
                - y_axis: List of correlation values for each bin
        """

        if self.verbose:
            print(f"Building correlogram with {self.n_walks} walks of length {self.walk_length}...")

        # Step 1: Build random walks by repeated mutation
        if self.verbose:
            print("Step 1: Generating random walks...")

        solutions = []
        fitnesses = []

        for walk_idx in range(self.n_walks):
            # Start with a random solution
            current_sol = self.op.create_ind()
            solutions.append(current_sol)
            fitnesses.append(self.op.evaluate_ind(current_sol))

            # Perform walk_length mutations
            for step in range(self.walk_length):
                current_sol = self.op.mutate_ind(current_sol)
                solutions.append(current_sol)
                fitnesses.append(self.op.evaluate_ind(current_sol))

            if self.verbose and (walk_idx + 1) % 10 == 0:
                print(f"  Completed {walk_idx + 1}/{self.n_walks} walks...")

        n_solutions = len(solutions)
        if self.verbose:
            print(f"  Total solutions generated: {n_solutions}")

        # Step 2: Compute fitness statistics
        if self.verbose:
            print("Step 2: Computing fitness statistics...")

        mean_fitness = np.mean(fitnesses)
        var_fitness = np.var(fitnesses)

        if self.verbose:
            print(f"  Mean fitness: {mean_fitness:.4f}")
            print(f"  Fitness variance: {var_fitness:.4f}")

        if var_fitness == 0:
            if self.verbose:
                print("Warning: Flat fitness landscape (variance = 0).")
            self.x_axis = []
            self.y_axis = []
            self.avg_distance = 0
            self.results = {}
            return [], []

        # Step 3: Compute pairwise distances and covariances
        if self.verbose:
            print("Step 3: Computing pairwise distances...")

        distances_list = []
        covariances_list = []

        n_pairs = n_solutions * (n_solutions - 1) // 2
        if self.verbose:
            print(f"  Computing {n_pairs} pairwise distances...")

        for i in range(n_solutions):
            for j in range(i + 1, n_solutions):
                # Compute distance
                dist = self.op.distance_ind(solutions[i], solutions[j])
                distances_list.append(dist)

                # Compute covariance contribution
                cov = (fitnesses[i] - mean_fitness) * (fitnesses[j] - mean_fitness)
                covariances_list.append(cov)

            if self.verbose and (i + 1) % 100 == 0:
                print(f"  Processed {i + 1}/{n_solutions} solutions...")

        distances_array = np.array(distances_list)
        covariances_array = np.array(covariances_list)

        # Step 4: Compute average distance
        self.avg_distance = np.mean(distances_array)
        max_distance = np.max(distances_array)

        if self.verbose:
            print(f"Step 4: Distance statistics:")
            print(f"  Average distance: {self.avg_distance:.4f}")
            print(f"  Max distance: {max_distance:.4f}")
            print(f"  Min distance: {np.min(distances_array):.4f}")

        # Step 5: Bin and compute correlations
        if self.verbose:
            print(f"Step 5: Binning distances into {self.n_bins} bins...")

        bin_edges = np.linspace(0, max_distance, self.n_bins + 1)
        bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2

        bin_indices = np.digitize(distances_array, bin_edges) - 1
        bin_indices = np.clip(bin_indices, 0, self.n_bins - 1)

        x_axis = []
        y_axis = []
        bin_counts = []

        for bin_idx in range(self.n_bins):
            mask = bin_indices == bin_idx
            count = np.sum(mask)

            if count > 0:
                avg_cov = np.mean(covariances_array[mask])
                correlation = avg_cov / var_fitness

                x_axis.append(bin_centers[bin_idx])
                y_axis.append(correlation)
                bin_counts.append(count)

        if self.verbose:
            print(f"  Non-empty bins: {len(x_axis)}/{self.n_bins}")

        # Store results
        self.x_axis = x_axis
        self.y_axis = y_axis
        self.results = {
            'n_solutions': n_solutions,
            'n_pairs': n_pairs,
            'mean_fitness': mean_fitness,
            'var_fitness': var_fitness,
            'std_fitness': np.sqrt(var_fitness),
            'avg_distance': self.avg_distance,
            'max_distance': max_distance,
            'min_distance': np.min(distances_array),
            'n_bins': self.n_bins,
            'bin_centers': x_axis,
            'correlations': y_axis,
            'bin_counts': bin_counts,
            'solutions': solutions,
            'fitnesses': fitnesses,
            'distances': distances_array,
            'covariances': covariances_array
        }

        if self.verbose:
            print("\nCorrelogram completed!")
            if len(y_axis) > 0:
                print(f"Correlation at distance=0: {y_axis[0]:.4f}")
                print(f"Correlation at avg distance: {np.interp(self.avg_distance, x_axis, y_axis):.4f}")

        return x_axis, y_axis

    def plot(self, title="Fitness-Distance Correlogram (Random Walks)"):
        """
        Plot the correlogram.

        Args:
            title (str): Plot title

        Raises:
            RuntimeError: If correlogram hasn't been computed yet
        """
        if self.x_axis is None:
            raise RuntimeError("Must call correlogram_walks() before plot()")

        if len(self.x_axis) == 0:
            print("No data to plot (flat landscape)")
            return

        plt.figure(figsize=(10, 6))
        plt.plot(self.x_axis, self.y_axis, 'b-o', linewidth=2, markersize=6)
        plt.axhline(y=0, color='k', linestyle='--', alpha=0.3)
        plt.axvline(x=self.avg_distance, color='r', linestyle='--', alpha=0.5,
                    label=f'Avg distance = {self.avg_distance:.2f}')

        plt.xlabel('Distance', fontsize=12)
        plt.ylabel('Fitness Correlation', fontsize=12)
        plt.title(title, fontsize=14)
        plt.ylim(-1, 1)
        plt.xlim(0, 2 * self.avg_distance)
        plt.grid(True, alpha=0.3)
        plt.legend()
        plt.tight_layout()
        plt.show()

    def get_results(self):
        """
        Get detailed results dictionary.

        Returns:
            dict: Dictionary containing all analysis results

        Raises:
            RuntimeError: If correlogram hasn't been computed yet
        """
        if self.results is None:
            raise RuntimeError("Must call correlogram_walks() before get_results()")

        return self.results
