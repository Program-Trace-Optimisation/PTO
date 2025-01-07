# GENETIC ALGORITHM

import math
import random


class genetic_algorithm:

    ##############
    # PARAMETERS #
    ##############

    def __init__(
        self,
        op,
        better=max,
        callback=None,
        n_generation=100,
        population_size=50,
        truncation_rate=0.5,
        mutation="mutate_position_wise_ind",
        crossover="crossover_one_point_ind",
        verbose=False,
        return_history=False,
    ):

        self.op = op
        self.better = better
        self.callback = callback
        self.n_generation = n_generation
        self.population_size = population_size
        self.truncation_rate = truncation_rate
        self.mutation = mutation
        self.crossover = crossover
        self.verbose = verbose
        self.return_history = return_history

        # set-up search operators
        self.op.mutate_ind = getattr(op, self.mutation)
        self.op.crossover_ind = getattr(op, self.crossover)

    #############
    # ALGORITHM #
    #############

    # run algorithm
    def __call__(self):

        population = self.create_pop()
        fitness_population = self.evaluate_pop(population)
        if self.return_history:
            self.history = []

        # online stats
        search_state = (population, fitness_population, 0)
        best = self.best_pop(population, fitness_population)
        if self.verbose:
            print(*best)
        if self.return_history:
            self.history.append(best[1])
        if self.callback:
            self.callback(search_state)

        for gen in range(self.n_generation):
            mating_pool = self.select_pop(population, fitness_population)
            offspring_population = self.crossover_pop(mating_pool)
            population = self.mutate_pop(offspring_population)
            population[0] = best[0]  # elitism
            fitness_population = self.evaluate_pop(population)

            search_state = (population, fitness_population, gen)
            best = self.best_pop(population, fitness_population)
            if self.verbose:
                print(*self.best_pop(population, fitness_population))
            if self.return_history:
                self.history.append(best[1])
            if self.callback and self.callback(search_state):
                break

        if self.return_history:
            return *best, self.history
        else:
            return best[0], best[1], gen

    #################
    # POP FUNCTIONS #
    #################

    def create_pop(self):
        return [self.op.create_ind() for _ in range(self.population_size)]

    def evaluate_pop(self, population):
        return [self.op.evaluate_ind(sol) for sol in population]

    def select_pop(self, population, fitness_population):
        sorted_population = sorted(
            zip(population, fitness_population),
            key=lambda ind_fit: ind_fit[1],
            reverse=(self.better == max),
        )
        return [
            individual
            for individual, fitness in sorted_population[
                : int(math.ceil(self.population_size * self.truncation_rate))
            ]
        ]

    def crossover_pop(self, population):
        return [
            self.op.crossover_ind(random.choice(population), random.choice(population))
            for _ in range(self.population_size)
        ]

    def mutate_pop(self, population):
        return [self.op.mutate_ind(sol) for sol in population]

    def best_pop(self, population, fitness_population):
        best_idx = self.better(
            range(len(fitness_population)), key=lambda i: fitness_population[i]
        )
        return population[best_idx], fitness_population[best_idx]


# def stats_pop(self, fitness_population = [0]):
#     return { 'MAX_FITNESS' : max(fitness_population), 'MIN_FITNESS' : min(fitness_population), 'AVG_FITNESS' : sum(fitness_population)/len(fitness_population) }

#############################
