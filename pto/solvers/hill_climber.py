# HILL CLIMBER

""" Search algorithms are generic without reference to the trace representation. """


class hill_climber:

    ##############
    # PARAMETERS #
    ##############

    def __init__(
        self,
        op,
        better=max,
        callback=None,
        n_generation=1000,
        mutation="mutate_position_wise_ind",
        verbose=False,
        return_history=False,
    ):

        self.op = op
        self.better = better
        self.callback = callback
        self.n_generation = n_generation
        self.mutation = mutation
        self.verbose = verbose
        self.return_history = return_history

        # set-up search operators
        self.op.mutate_ind = getattr(op, self.mutation)

    #############
    # ALGORITHM #
    #############

    # run algorithm
    def __call__(self):

        # initial solution
        individual = self.op.create_ind()
        fitness_individual = self.op.evaluate_ind(individual)

        if self.return_history:
            self.history = []

        # online stats
        search_state = (individual, fitness_individual, 0)
        if self.verbose:
            print(*search_state)
        if self.return_history:
            self.history.append(search_state[1])
        if self.callback:
            self.callback(search_state)

        for gen in range(self.n_generation):

            offspring = self.op.mutate_ind(individual)
            fitness_offspring = self.op.evaluate_ind(offspring)

            individual, fitness_individual = self.better(
                [(individual, fitness_individual), (offspring, fitness_offspring)],
                key=lambda x: x[1],
            )

            search_state = (individual, fitness_individual, gen)
            if self.verbose:
                print(*search_state)
            if self.return_history:
                self.history.append(search_state[1])
            if self.callback and self.callback(search_state):
                break

        if self.return_history:
            return search_state[0], search_state[1], self.history
        else:
            return search_state  # return result object?


# ---------------
