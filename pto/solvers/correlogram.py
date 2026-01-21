import math
import random
import numpy as np
from skgstat import Variogram, MetricSpace
try:
    from scipy import stats
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False


class correlogram:

    ##############
    # PARAMETERS #
    ##############

    def __init__(
        self,
        op,
        avg_dist_tolerance=0.1,  # In preliminary sampling: continue sampling pairs til avg_distance converges to within this
        n_samples=20, 
        mutate="mutate_ind",
        distance="distance_ind",  # The name of the distance function in 'op'
        verbose=False,
        n_bins=None,  # Number of bins for distance binning (default: walk_len)
        bin_width=None,  # Alternative: specify bin width instead of n_bins
        min_pairs_per_bin=5,  # Minimum pairs required for reliable correlation estimate
        run_structural_mutation_filter=False, # some generators benefit from an extra analysis - switch it on manually if needed
        **kwargs,
    ):
        self.op = op
        self.avg_dist_tolerance = avg_dist_tolerance
        self.n_samples = n_samples
        self.mutate_func_name = mutate
        self.distance_func_name = distance
        self.verbose = verbose
        self.n_bins = n_bins
        self.bin_width = bin_width
        self.min_pairs_per_bin = min_pairs_per_bin
        self.run_structural_mutation_filter = run_structural_mutation_filter

        # Set-up search operators
        # We assume op has create_ind, evaluate_ind, and the distance function
        self.op.mutate_ind = getattr(op, self.mutate_func_name)
        self.op.distance_ind = getattr(op, self.distance_func_name)


    #############
    # ALGORITHM #
    #############

    # Run the analysis
    def __call__(self):

        # 1. Calculate avg_dist in the space
        if self.verbose:
            print(f"Calculating avg_dist...")
        avg_dist = self.avg_dist() # avg distance between pair
        diameter = avg_dist * 2
        walk_len = 20 # TODO should we incorporate diameter here?
        self.n_walks = self.n_samples // walk_len
        

        # 2. Run some random walks to collect individuals
        # and evaluate them
        if self.verbose:
            print("Running random walks and evaluating population")
        population, walks = self.run_random_walks(walk_len)
        fitness = self.evaluate_pop(population)

        # Calculate one-step correlation from consecutive steps in walks
        onestep_correlations = []
        for walk_indices in walks:
            walk_fitness = [fitness[i] for i in walk_indices]
            if len(walk_fitness) >= 2:
                # Correlation between f_i and f_{i+1} within this walk
                f_i = walk_fitness[:-1]  # all but last
                f_i_plus_1 = walk_fitness[1:]  # all but first
                if len(f_i) >= 2:  # need at least 2 pairs
                    r = np.corrcoef(f_i, f_i_plus_1)[0, 1]
                    if not np.isnan(r):
                        onestep_correlations.append(r)

        # Average one-step correlation across all walks
        if len(onestep_correlations) > 0:
            onestep_cor = np.mean(onestep_correlations)
        else:
            onestep_cor = np.nan


        # 3. Compute Pairwise Distances and Correlations
        if self.verbose:
            print("Computing pairwise distances...")

        records = []
        for i in range(len(population)):
            for j in range(i + 1, len(population)):
                # Use the provided distance_ind function
                dist = self.op.distance_ind(population[i], population[j])

                records.append((fitness[i], fitness[j], dist))
        records = np.array(records)

        # 4. Bins and correlations
        def correlation_with_pvalue(a, b):
            """Calculate correlation coefficient and p-value"""
            if HAS_SCIPY:
                try:
                    r, p = stats.pearsonr(a, b)
                    return r, p
                except (FloatingPointError, ValueError):
                    # Handle numerical issues with very strong correlations
                    r = np.corrcoef(a, b)[0, 1]
                    # If correlation is very strong and sample is large, p-value is effectively 0
                    if len(a) > 100 and abs(r) > 0.99:
                        p = 0.0
                    else:
                        p = np.nan
                    return r, p
            else:
                # Fallback: compute correlation, estimate p-value manually
                r = np.corrcoef(a, b)[0, 1]
                # Simple p-value approximation using t-distribution
                n = len(a)
                if n > 2:
                    t = r * np.sqrt((n - 2) / (1 - r**2 + 1e-10))
                    # Two-tailed p-value approximation
                    p = 2 * (1 - np.clip(np.abs(t) / np.sqrt(n), 0, 1))
                else:
                    p = np.nan
                return r, p

        # Check if distances are all integers
        distances = records[:, 2]
        all_integers = np.all(distances == np.floor(distances))

        # Determine if we should use binning
        use_binning = (self.n_bins is not None) or (self.bin_width is not None) or (not all_integers)

        x_axis = []
        y_axis = []
        p_axis = []
        n_axis = []

        if use_binning:
            # Use binning for real-valued distances
            if self.verbose:
                print(f"Using binning for real-valued distances...")

            min_dist = np.min(distances)
            max_dist = np.max(distances)

            if self.bin_width is not None:
                # Use specified bin width
                n_bins = int(np.ceil((max_dist - min_dist) / self.bin_width))
            elif self.n_bins is not None:
                # Use specified number of bins
                n_bins = self.n_bins
            else:
                # Default
                n_bins = 10 # not walk_len because eg with fine dist we may have a small avg_dist

            # Create bin edges and centers
            bin_edges = np.linspace(min_dist, max_dist, n_bins + 1)
            bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2

            for i in range(len(bin_centers)):
                # Get pairs within this bin
                lower = bin_edges[i]
                upper = bin_edges[i + 1]

                # Include upper edge only for the last bin
                if i == len(bin_centers) - 1:
                    mask = (distances >= lower) & (distances <= upper)
                else:
                    mask = (distances >= lower) & (distances < upper)

                pairs = records[mask][:, :2]

                if self.verbose:
                    print(f"Bin {i+1}/{len(bin_centers)}: [{lower:.2f}, {upper:.2f}), center={bin_centers[i]:.2f}, pairs={len(pairs)}")

                n_pairs = len(pairs)
                n_axis.append(n_pairs)

                if n_pairs < self.min_pairs_per_bin:
                    y_axis.append(np.nan)
                    p_axis.append(np.nan)
                else:
                    r, p = correlation_with_pvalue(pairs[:, 0], pairs[:, 1])
                    y_axis.append(r)
                    p_axis.append(p)
                x_axis.append(bin_centers[i])

            # Add a final bin for distances beyond the last bin edge
            pairs = records[distances > bin_edges[-1]][:, :2]
            n_pairs = len(pairs)
            if n_pairs >= self.min_pairs_per_bin:
                # Use a distance slightly beyond the last bin center
                x_axis.append(bin_centers[-1] + (bin_edges[-1] - bin_centers[-1]))
                r, p = correlation_with_pvalue(pairs[:, 0], pairs[:, 1])
                y_axis.append(r)
                p_axis.append(p)
                n_axis.append(n_pairs)

        else:
            # Use exact integer distances (original behavior)
            if self.verbose:
                print(f"Using exact integer distances...")

            for d in range(1, walk_len + 1):
                # correlation of the fi, fj values of a given distance
                if self.verbose:
                    print(f"computing for {d}")
                pairs = records[distances == d][:, :2]
                n_pairs = len(pairs)
                if self.verbose:
                    print(f"number of pairs {n_pairs}")
                n_axis.append(n_pairs)
                if n_pairs < self.min_pairs_per_bin:
                    y_axis.append(np.nan)
                    p_axis.append(np.nan)
                else:
                    r, p = correlation_with_pvalue(pairs[:, 0], pairs[:, 1])
                    y_axis.append(r)
                    p_axis.append(p)
                x_axis.append(d)

            # correlation of the fi, fj values greater than the max distance
            d = walk_len + 1
            pairs = records[distances >= d][:, :2]
            n_pairs = len(pairs)
            if n_pairs >= self.min_pairs_per_bin:
                x_axis.append(d)
                r, p = correlation_with_pvalue(pairs[:, 0], pairs[:, 1])
                y_axis.append(r)
                p_axis.append(p)
                n_axis.append(n_pairs)

        # Filter out NaN values before calculating correlation length
        x_axis_filtered = []
        y_axis_filtered = []
        for x, y in zip(x_axis, y_axis):
            if not np.isnan(y):
                x_axis_filtered.append(x)
                y_axis_filtered.append(y)

        # Calculate correlation length only if we have valid data
        if len(x_axis_filtered) > 1:
            cor_len = self.correlation_length(x_axis_filtered, y_axis_filtered)
        else:
            cor_len = np.nan

        # TODO
        if use_binning:
            n_lags = 20
        else:
            n_lags = 20

        (g_avg_dist, g_total_var, 
         g_norm_corr_length, g_nugget, variogram) = self.make_variogram(
             population, fitness, n_lags, self.op.distance_ind, 
             model='spherical')
        
        if self.run_structural_mutation_filter:
            n = 10000
            min_len = 0
            sr_structural_change_cor, sr_average_parent_length = self.analyze_mutation_operator(n, min_len)
        else:
            sr_structural_change_cor, sr_average_parent_length = 0, 0

        return (x_axis, y_axis, p_axis, n_axis, # after binning: x; y cor; p cor p-value; n num per bin
                cor_len, diameter, onestep_cor, # cor_len calculated using crossing; diameter; one-step cor by one-mutation
                sr_structural_change_cor, sr_average_parent_length, # stats from filtered mutation method, ie filter for structural change
                g_avg_dist, g_total_var, g_norm_corr_length, g_nugget, # stats from geostats Variogram method
                variogram) 

    ###################
    # EXTRA FUNCTIONS #
    ###################

    def create_pop(self, size):
        return [self.op.create_ind() for _ in range(size)]

    def evaluate_pop(self, population):
        return [self.op.evaluate_ind(sol) for sol in population]
        
    def run_random_walks(self, walk_len):
        pop = []
        walks = []  # Store indices for each walk
        for i in range(self.n_walks):
            walk_indices = []
            x = self.op.create_ind()
            pop.append(x)
            walk_indices.append(len(pop) - 1)
            for j in range(walk_len - 1):
                x = self.op.mutate_ind(x)
                pop.append(x)
                walk_indices.append(len(pop) - 1)
            walks.append(walk_indices)
        return pop, walks
    
    def avg_dist(self):
        """
        Estimate average distance between random individuals by sampling pairs
        """
        dists = []
        prev_avg = 0

        while True:
            # Sample a pair
            x, y = [self.op.create_ind() for _ in range(2)]
            d = self.op.distance_ind(x, y)
            dists.append(d)

            # Check convergence every 100 samples
            if len(dists) % 100 == 0:
                avg = np.mean(dists)
                if len(dists) >= 200 and abs(avg - prev_avg) < self.avg_dist_tolerance:
                    if self.verbose:
                        print(f"avg_dist converged after {len(dists)} samples: {avg:.4f}")
                    return avg
                prev_avg = avg

            # Safety: max samples
            if len(dists) >= 10000:
                if self.verbose:
                    print(f"avg_dist reached max samples (10000): {np.mean(dists):.4f}")
                return np.mean(dists)
    
    def correlation_length(self, x_axis, y_axis, threshold=0.01):
        """
        Calculate the correlation length: the distance where correlation drops below some threshold

        Args:
            x_axis: array-like of distance values (must not contain NaN)
            y_axis: array-like of correlation values (must not contain NaN)
            threshold: threshold value for correlation

        Returns:
            float: The distance where correlation drops below threshold, or np.nan if cannot be determined
        """

        # Convert to numpy arrays for easier manipulation
        x = np.array(x_axis)
        y = np.array(y_axis)

        if self.verbose:
            print(f"Correlation values: {y_axis}")

        # Handle edge cases
        if len(x) < 2:
            if self.verbose:
                print("Not enough data points to calculate correlation length")
            return np.nan

        if y[0] <= threshold:
            if self.verbose:
                print(f"First correlation value {y[0]:.3f} is already below threshold {threshold}")
            return x[0]

        # Find where correlation crosses the threshold
        for i in range(len(y) - 1):
            if y[i] >= threshold and y[i+1] < threshold:
                # Linear interpolation between the two points
                x1, y1 = x[i], y[i]
                x2, y2 = x[i+1], y[i+1]
                # Solve for x where y = threshold
                cor_len = x1 + (threshold - y1) * (x2 - x1) / (y2 - y1)
                return cor_len

        if self.verbose:
            print(f"Last correlation value {y[-1]:.3f} is still above threshold {threshold}")
        return np.max(x)
        
        # If threshold not crossed, return the max distance
        return np.max(x)


    def analyze_mutation_operator(self, num_iterations=10000, min_len=0):
        parent_fitnesses = []
        offspring_fitnesses = []
        parent_geno_lengths = []

        for _ in range(num_iterations):
            parent_sol = None
            # Retry generating parent solution until its genotype length is at least min_len
            while parent_sol is None or len(parent_sol.geno) < min_len:
                parent_sol = self.op.create_ind()

            # 2. Mutate the parent solution to create an offspring
            offspring_sol = self.op.mutate_ind(parent_sol)
            # Resample offspring until its genotype length is different from parent's
            while len(offspring_sol.geno) == len(parent_sol.geno):
                offspring_sol = self.op.mutate_ind(parent_sol)

            # 3. Compute the fitness for both parent and offspring
            parent_fit = self.op.evaluate_ind(parent_sol)
            offspring_fit = self.op.evaluate_ind(offspring_sol)

            parent_fitnesses.append(parent_fit)
            offspring_fitnesses.append(offspring_fit)

            # Get length of parent genotype (trace)
            parent_geno_lengths.append(len(parent_sol.geno))

        # 5. Compute the correlation between parent and offspring fitness
        correlation = np.corrcoef(parent_fitnesses, offspring_fitnesses)[0, 1]

        # 6. Return the average length of parent trace
        average_parent_length = np.mean(parent_geno_lengths)

        return correlation, average_parent_length
    
    



    # model='exponential', 'spherical'
    def make_variogram(self, x, y, n_lags, dist, model='spherical'):
        # copied from https://colab.research.google.com/drive/13rUkHW3DxhkRR6ZjujGjfvmp3N0U1hix

        n = len(x)
        dist_matrix = np.zeros((n, n))
        for i in range(n):
            for j in range(n):
                dist_matrix[i, j] = dist(x[i], x[j])
        dummy = np.random.random((n, 2)) # we will over-write                
        ms = MetricSpace(dummy) 
        ms._dists = dist_matrix

        # 3. ANALYSIS
        # Increasing n_lags helps capture the fine-grained scatter
        V = Variogram(
            coordinates=ms,
            values=y,
            n_lags=n_lags,
            model=model,
            filename=None
        )

        # 4. NORMALIZATION
        avg_dist = np.mean(V.distance)
        total_variance = np.var(y)

        # 6. OUTPUT STATS
        norm_corr_length = V.parameters[0] / avg_dist
        # print(f"Normalized Correlation Length (Range): {norm_corr_length:.4f}")
        # print(f"Nugget (Local Discontinuity): {V.parameters[2]:.4f}")  
        return avg_dist, total_variance, norm_corr_length, V.parameters[2], V


 
        

