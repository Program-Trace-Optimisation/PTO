import math
import random

class novelty_search:
    def __init__(self, op, *, behavior_distance, better=max, callback=None,
                 n_generation=100, population_size=50, archive_size=1000,
                 k_nearest=15, local_competition_radius=None,
                 selection_pressure=0.5, truncation_rate=0.5,
                 mutation='mutate_position_wise_ind',
                 crossover='crossover_one_point_ind',
                 verbose=False, return_history=False):
        """
        Novelty Search with Local Competition implementation.
        
        Args:
            op: Operator class containing problem-specific functions
            behavior_distance: Function that computes behavioral distance between two individuals
            better: Function to determine if maximizing or minimizing (default: max)
            callback: Optional callback function called after each generation
            n_generation: Number of generations to run
            population_size: Size of population
            archive_size: Maximum size of novelty archive
            k_nearest: Number of nearest neighbors for novelty computation
            local_competition_radius: Radius for local competition (if None, uses average distance)
            selection_pressure: Balance between novelty and local competition (0-1)
            truncation_rate: Fraction of population selected for breeding
            mutation: Name of mutation operator in op class
            crossover: Name of crossover operator in op class
            verbose: Whether to print progress
            return_history: Whether to return history of evolution
        """
        self.op = op
        self.behavior_distance = behavior_distance
        self.better = better
        self.callback = callback
        self.n_generation = n_generation
        self.population_size = population_size
        self.archive_size = archive_size
        self.k_nearest = min(k_nearest, population_size + archive_size - 1)
        self.local_competition_radius = local_competition_radius
        self.selection_pressure = selection_pressure
        self.truncation_rate = truncation_rate
        self.mutation = mutation
        self.crossover = crossover
        self.verbose = verbose
        self.return_history = return_history
        
        # Archive for novelty search
        self.archive = []
        
        # Set up search operators
        self.op.mutate_ind = getattr(op, self.mutation)
        self.op.crossover_ind = getattr(op, self.crossover)

    def __call__(self):
        population = self.create_pop()
        fitness_population = self.evaluate_pop(population)
        if self.return_history:
            self.history = []
        
        # Calculate initial metrics
        novelty_scores = self.compute_novelty_all(population)
        local_comp_scores = self.compute_local_competition_all(population, fitness_population)
        
        # Online stats
        search_state = (population, fitness_population, 0) 
        best = self.best_pop(population, fitness_population)
        if self.verbose:
            print(f"Gen 0 - Best Fitness: {best[1]}, "
                  f"Avg Novelty: {sum(novelty_scores)/len(novelty_scores):.2f}, "
                  f"Avg Local Comp: {sum(local_comp_scores)/len(local_comp_scores):.2f}")
        if self.return_history:
            self.history.append((best[1], novelty_scores, local_comp_scores))
        if self.callback:
            self.callback(search_state)
        
        for gen in range(self.n_generation):
            # Update archive before selection
            self.update_archive(population, novelty_scores)
            
            # Selection using both novelty and local competition
            mating_pool = self.select_pop(population, novelty_scores, local_comp_scores)
            offspring_population = self.crossover_pop(mating_pool)
            population = self.mutate_pop(offspring_population)
            population[0] = best[0]  # elitism
            
            # Evaluate new population
            fitness_population = self.evaluate_pop(population)
            novelty_scores = self.compute_novelty_all(population)
            local_comp_scores = self.compute_local_competition_all(population, fitness_population)
            
            search_state = (population, fitness_population, gen) 
            best = self.best_pop(population, fitness_population)
            
            if self.verbose:
                print(f"Gen {gen+1} - Best Fitness: {best[1]}, "
                      f"Avg Novelty: {sum(novelty_scores)/len(novelty_scores):.2f}, "
                      f"Avg Local Comp: {sum(local_comp_scores)/len(local_comp_scores):.2f}")
            if self.return_history:
                self.history.append((best[1], novelty_scores, local_comp_scores))
            if self.callback and self.callback(search_state):
                break
        
        if self.return_history:
            return *best, self.history
        else:
            return best[0], best[1], gen
    
    def create_pop(self):
        """Create initial population."""
        return [self.op.create_ind() for _ in range(self.population_size)]
    
    def evaluate_pop(self, population):
        """Evaluate fitness of population."""
        return [self.op.evaluate_ind(sol) for sol in population]
    
    def compute_novelty(self, individual, population):
        """Compute novelty score for an individual."""
        # Combine current population and archive
        all_individuals = population + self.archive
        
        # Calculate distances to all other individuals
        distances = [self.behavior_distance(individual, other) 
                    for other in all_individuals if other is not individual]
        
        if not distances:
            return 0.0
        
        # Sort distances and compute average of k nearest
        distances.sort()
        k = min(self.k_nearest, len(distances))
        return sum(distances[:k]) / k
    
    def compute_novelty_all(self, population):
        """Compute novelty scores for entire population."""
        return [self.compute_novelty(ind, population) for ind in population]
    
    def compute_local_competition(self, individual, index, population, fitness_population):
        """Compute local competition score for an individual."""
        all_individuals = population + self.archive
        all_fitness = fitness_population + [self.op.evaluate_ind(ind) for ind in self.archive]
        
        # Determine local competition radius if not set
        if self.local_competition_radius is None:
            distances = [self.behavior_distance(individual, other)
                        for other in all_individuals if other is not individual]
            radius = sum(distances) / len(distances) if distances else 1.0
        else:
            radius = self.local_competition_radius
        
        # Find neighbors within radius
        neighbors_indices = [i for i, other in enumerate(all_individuals)
                           if i != index and 
                           self.behavior_distance(individual, other) < radius]
        
        if not neighbors_indices:
            return 0.0
        
        # Count individuals outperformed in local neighborhood
        ind_fitness = all_fitness[index]
        better_count = sum(1 for i in neighbors_indices 
                          if self.better(ind_fitness, all_fitness[i]) == ind_fitness)
        
        return better_count / len(neighbors_indices)
    
    def compute_local_competition_all(self, population, fitness_population):
        """Compute local competition scores for entire population."""
        return [self.compute_local_competition(ind, i, population, fitness_population)
                for i, ind in enumerate(population)]
    
    def update_archive(self, population, novelty_scores):
        """Update archive with novel individuals."""
        for ind, score in zip(population, novelty_scores):
            if len(self.archive) < self.archive_size:
                self.archive.append(ind)
            elif score > min(novelty_scores):
                # Replace least novel member
                min_idx = novelty_scores.index(min(novelty_scores))
                self.archive[min_idx] = ind
    
    def select_pop(self, population, novelty_scores, local_comp_scores):
        """Select individuals based on both novelty and local competition."""
        # Combine scores using selection pressure parameter
        combined_scores = [self.selection_pressure * n + (1 - self.selection_pressure) * l
                         for n, l in zip(novelty_scores, local_comp_scores)]
        
        # Sort population by combined scores
        sorted_population = sorted(zip(population, combined_scores),
                                 key=lambda x: x[1],
                                 reverse=True)
        
        # Select top portion based on truncation rate
        return [ind for ind, _ in 
                sorted_population[:int(math.ceil(self.population_size * self.truncation_rate))]]
    
    def crossover_pop(self, population):
        """Create offspring through crossover."""
        return [self.op.crossover_ind(random.choice(population),
                                    random.choice(population))
                for _ in range(self.population_size)]
    
    def mutate_pop(self, population):
        """Apply mutation to population."""
        return [self.op.mutate_ind(sol) for sol in population]
    
    def best_pop(self, population, fitness_population):
        """Find best individual in population."""
        best_idx = self.better(range(len(fitness_population)),
                             key=lambda i: fitness_population[i])
        return population[best_idx], fitness_population[best_idx]

#### TEST ON BINARY STRINGS

# Define behavior distance metric
def my_behavior_distance(ind1, ind2):
    # Return float representing behavioral distance
    # Example for bit strings:
    return sum(a != b for a, b in zip(ind1, ind2))

class BinaryProblem:
    def __init__(self, n_dimensions):
        self.n_dimensions = n_dimensions

    def create_ind(self):
        return [random.randint(0, 1) for _ in range(self.n_dimensions)]

    def evaluate_ind(self, individual):
        return sum(individual)  # Example: maximize the number of 1's
    
    def mutate_position_wise_ind(self, individual):
        for i in range(len(individual)):
            if random.random() < 1/len(individual):
                individual[i] = 1 - individual[i]
        return individual
    
    def crossover_one_point_ind(self, parent1, parent2):
        point = random.randint(1, len(parent1)-1)  # Exclude endpoints
        return parent1[:point] + parent2[point:]
    
# Example usage:
if __name__ == "__main__":
    #random.seed(42)  # for reproducibility
    op = BinaryProblem(n_dimensions=50)
    nslc = novelty_search(op=op, behavior_distance=my_behavior_distance, population_size=50, n_generation=100)
    best_solution, best_fitness, generations = nslc()
    print(f"Best solution: {best_solution}")
    print(f"Best fitness: {best_fitness}")
    print(f"Generations: {generations}")