import math
import random
import numpy as np


class correlogram:

    ##############
    # PARAMETERS #
    ##############

    def __init__(
        self,
        op,
        avg_dist_tolerance=0.1,  # In preliminary sampling: continue sampling pairs til avg_distance converges to within this
        n_samples=1000, 
        mutate="mutate_ind",
        distance="distance_ind",  # The name of the distance function in 'op'
        verbose=False,
        n_bins=None,  # Number of bins for distance binning (default: walk_len)
        bin_width=None,  # Alternative: specify bin width instead of n_bins
        min_pairs_per_bin=10,  # Minimum pairs required for reliable correlation estimate
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

        self.batch_size = 100

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
            print(f"Sampling batches of {self.batch_size} solutions...")
        avg_dist = self.avg_dist() # avg distance between pair
        diameter = avg_dist * 2
        walk_len = max(int(diameter), 20) # TODO
        self.n_walks = self.n_samples // walk_len
        

        # 2. Run some random walks to collect individuals
        # and evaluate them
        if self.verbose:
            print("Running random walks and evaluating population")
        population = self.run_random_walks(walk_len)
        fitness = self.evaluate_pop(population)


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
        def correlation(a, b): return np.corrcoef(a, b)[0, 1]

        # Check if distances are all integers
        distances = records[:, 2]
        all_integers = np.all(distances == np.floor(distances))

        # Determine if we should use binning
        use_binning = (self.n_bins is not None) or (self.bin_width is not None) or (not all_integers)

        x_axis = []
        y_axis = []

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

                if len(pairs) < self.min_pairs_per_bin:
                    y_axis.append(np.nan)
                else:
                    y_axis.append(correlation(pairs[:, 0], pairs[:, 1]))
                x_axis.append(bin_centers[i])

            # Add a final bin for distances beyond the last bin edge
            pairs = records[distances > bin_edges[-1]][:, :2]
            if len(pairs) >= self.min_pairs_per_bin:
                # Use a distance slightly beyond the last bin center
                x_axis.append(bin_centers[-1] + (bin_edges[-1] - bin_centers[-1]))
                y_axis.append(correlation(pairs[:, 0], pairs[:, 1]))

        else:
            # Use exact integer distances (original behavior)
            if self.verbose:
                print(f"Using exact integer distances...")

            for d in range(1, walk_len + 1):
                # correlation of the fi, fj values of a given distance
                if self.verbose:
                    print(f"computing for {d}")
                pairs = records[distances == d][:, :2]
                if self.verbose:
                    print(f"number of pairs {len(pairs)}")
                if len(pairs) < self.min_pairs_per_bin:
                    y_axis.append(np.nan)
                else:
                    y_axis.append(correlation(pairs[:, 0], pairs[:, 1]))
                x_axis.append(d)

            # correlation of the fi, fj values greater than the max distance
            d = walk_len + 1
            pairs = records[distances >= d][:, :2]
            if len(pairs) >= self.min_pairs_per_bin:
                x_axis.append(d)
                y_axis.append(correlation(pairs[:, 0], pairs[:, 1]))

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

        return x_axis, y_axis, cor_len, diameter


    ###################
    # EXTRA FUNCTIONS #
    ###################

    def create_pop(self, size):
        return [self.op.create_ind() for _ in range(size)]

    def evaluate_pop(self, population):
        return [self.op.evaluate_ind(sol) for sol in population]
        
    def run_random_walks(self, walk_len):
        pop = []
        for i in range(self.n_walks):
            x = self.op.create_ind()
            pop.append(x)
            for j in range(walk_len - 1):
                x = self.op.mutate_ind(x)
                pop.append(x)
        return pop
    
    def avg_dist(self):
        """
        Moving average of distance over pairs
        
        
        """
        delta = 1e6
        # initial large sample
        dists = []
        pop = [self.op.create_ind() for _ in range(100)]
        for i in range(len(pop)):
            for j in range(i + 1, len(pop)):
                d = self.op.distance_ind(pop[i], pop[j])
                dists.append(d)
        avg = np.mean(dists)
        n = 100
        # keep sampling until we converge
        while delta > self.avg_dist_tolerance:
            x, y = [self.op.create_ind() for _ in range(2)]
            d = self.op.distance_ind(x, y)
            newavg = avg + (d - avg) / n
            delta = abs(newavg - avg)
            avg = newavg
            n += 1
        return avg
    
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

