import random

class PSO:
    def __init__(self, op, better=max, callback=None, n_iteration=100, n_particles=50, w1=0.3, w2=0.3, w3=0.4, mutation_rate=0.01, verbose=False):
        self.op = op
        self.better = better
        self.callback = callback
        self.n_iteration = n_iteration
        self.n_particles = n_particles
        self.w1 = w1  # weight for current position
        self.w2 = w2  # weight for personal best
        self.w3 = w3  # weight for global best
        self.mutation_rate = mutation_rate
        self.verbose = verbose

    def __call__(self):
        swarm = self.create_swarm()
        fitness_swarm = self.evaluate_swarm(swarm)
        personal_best = swarm.copy()
        fitness_personal_best = fitness_swarm.copy()
        global_best, fitness_global_best = self.best_swarm(swarm, fitness_swarm)
        
        search_state = (swarm, fitness_swarm, personal_best, fitness_personal_best, global_best, fitness_global_best)
        if self.verbose: print(f"Initial best: {global_best}, fitness: {fitness_global_best}")
        if self.callback: self.callback(search_state)
    
        for i in range(self.n_iteration):
            swarm = self.update_swarm(swarm, personal_best, global_best)
            swarm = self.mutate_swarm(swarm)
            fitness_swarm = self.evaluate_swarm(swarm)
            
            personal_best, fitness_personal_best = self.update_personal_best(swarm, fitness_swarm, personal_best, fitness_personal_best)
            global_best, fitness_global_best = self.update_global_best(personal_best, fitness_personal_best, global_best, fitness_global_best)
        
            search_state = (swarm, fitness_swarm, personal_best, fitness_personal_best, global_best, fitness_global_best)
            if self.verbose and (i + 1) % 10 == 0: 
                print(f"Iteration {i + 1}: Best fitness: {fitness_global_best}")
            if self.callback and self.callback(search_state): break            

        return global_best, fitness_global_best
    
    def create_swarm(self):
        return [self.op.create_ind() for _ in range(self.n_particles)]

    def evaluate_swarm(self, swarm):
        return [self.op.evaluate_ind(sol) for sol in swarm]

    def update_swarm(self, swarm, personal_best, global_best):
        return [self.op.convex_crossover_ind(swarm[i], personal_best[i], global_best) for i in range(self.n_particles)]

    def mutate_swarm(self, swarm):
        return [self.op.mutate_ind(sol) for sol in swarm]

    def update_personal_best(self, swarm, fitness_swarm, personal_best, fitness_personal_best):
        for i in range(self.n_particles):
            if self.better(fitness_swarm[i], fitness_personal_best[i]) == fitness_swarm[i]:
                personal_best[i] = swarm[i]
                fitness_personal_best[i] = fitness_swarm[i]
        return personal_best, fitness_personal_best

    def update_global_best(self, personal_best, fitness_personal_best, global_best, fitness_global_best):
        best_idx = self.better(range(len(fitness_personal_best)), key=lambda i: fitness_personal_best[i]) 
        if self.better(fitness_personal_best[best_idx], fitness_global_best) == fitness_personal_best[best_idx]:
            return personal_best[best_idx], fitness_personal_best[best_idx]
        return global_best, fitness_global_best

    def best_swarm(self, swarm, fitness_swarm):
        best_idx = self.better(range(len(fitness_swarm)), key=lambda i: fitness_swarm[i])
        return swarm[best_idx], fitness_swarm[best_idx]

#### TEST ON BINARY STRINGS

class BinaryProblem:
    def __init__(self, n_dimensions):
        self.n_dimensions = n_dimensions

    def create_ind(self):
        return [random.randint(0, 1) for _ in range(self.n_dimensions)]

    def evaluate_ind(self, individual):
        return sum(individual)  # Example: maximize the number of 1's
    
    def convex_crossover_ind(self, individual1, individual2, individual3, weights=[0.3, 0.3, 0.4]):
        new_individual = []
        for i in range(self.n_dimensions):
            r = random.random()
            if r < weights[0]:
                new_individual.append(individual1[i])
            elif r < weights[0] + weights[1]:
                new_individual.append(individual2[i])
            else:
                new_individual.append(individual3[i])
        return new_individual
    
    def mutate_ind(self, individual, mutation_rate=0.01):
        for i in range(len(individual)):
            if random.random() < mutation_rate:
                individual[i] = 1 - individual[i]
        return individual

# Example usage:
if __name__ == "__main__":
    #random.seed(42)  # for reproducibility
    op = BinaryProblem(n_dimensions=50)
    pso = PSO(op, better=max, n_iteration=100, n_particles=50, verbose=True)
    best_solution, best_fitness = pso()
    print(f"Best solution: {best_solution}")
    print(f"Best fitness: {best_fitness}")


