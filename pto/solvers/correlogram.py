import math
import random


class correlogram:

    ##############
    # PARAMETERS #
    ##############

    def __init__(
        self,
        op,
        sample_size=200,  # Number of random solutions to sample
        n_bins=20,  # Resolution of the correlogram
        distance="distance_ind",  # The name of the distance function in 'op'
        verbose=False,
    ):
        self.op = op
        self.sample_size = sample_size
        self.n_bins = n_bins
        self.distance_func_name = distance
        self.verbose = verbose

        # Set-up search operators
        # We assume op has create_ind, evaluate_ind, and the distance function
        self.op.distance_ind = getattr(op, self.distance_func_name)

    #############
    # ALGORITHM #
    #############

    # Run the analysis
    def __call__(self):

        # 1. Create a random sample of the landscape
        if self.verbose:
            print(f"Sampling {self.sample_size} solutions...")
        population = self.create_pop()

        # 2. Evaluate fitness
        fitness_population = self.evaluate_pop(population)

        # Calculate global mean and variance for normalization
        mean_f = sum(fitness_population) / len(fitness_population)
        var_f = sum((f - mean_f) ** 2 for f in fitness_population) / len(
            fitness_population
        )

        # Avoid division by zero if all fitnesses are identical (flat landscape)
        if var_f == 0:
            if self.verbose:
                print("Warning: Flat landscape (Variance is 0).")
            return [], []

        # 3. Compute Pairwise Distances and Correlations
        if self.verbose:
            print("Computing pairwise distances...")

        pairs_data = []  # Stores tuples of (distance, fitness_product)
        max_dist = 0.0

        for i in range(len(population)):
            for j in range(i + 1, len(population)):
                # Use the provided distance_ind function
                dist = self.op.distance_ind(population[i], population[j])

                # Calculate the product of deviations from the mean
                # (f_i - mean) * (f_j - mean)
                cov = (fitness_population[i] - mean_f) * (
                    fitness_population[j] - mean_f
                )

                pairs_data.append((dist, cov))
                if dist > max_dist:
                    max_dist = dist

        # 4. Binning the data
        if self.verbose:
            print(f"Binning data (Max distance: {max_dist})...")

        # Create bins
        bin_width = max_dist / self.n_bins if max_dist > 0 else 1
        bins = [0.0] * self.n_bins
        counts = [0] * self.n_bins

        for dist, cov in pairs_data:
            # Determine which bin this pair belongs to
            bin_idx = int(dist // bin_width)

            # Handle the edge case where dist == max_dist (put in last bin)
            if bin_idx >= self.n_bins:
                bin_idx = self.n_bins - 1

            bins[bin_idx] += cov
            counts[bin_idx] += 1

        # 5. Calculate Autocorrelation for each bin
        # rho(d) = Average(Covariance) / Variance

        x_axis = []  # Distance centers
        y_axis = []  # Correlation values

        for k in range(self.n_bins):
            if counts[k] > 0:
                avg_cov = bins[k] / counts[k]
                correlation = avg_cov / var_f

                # Center of the bin for plotting
                center_dist = (k * bin_width) + (bin_width / 2)

                x_axis.append(center_dist)
                y_axis.append(correlation)

        return x_axis, y_axis

    #################
    # POP FUNCTIONS #
    #################

    def create_pop(self):
        return [self.op.create_ind() for _ in range(self.sample_size)]

    def evaluate_pop(self, population):
        return [self.op.evaluate_ind(sol) for sol in population]
