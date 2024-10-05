
# HILL CLIMBER

''' Search algorithms are generic without reference to the trace representation. '''

class hill_climber:
    
    ##############
    # PARAMETERS #
    ##############
    
    def __init__(self, op, better=max, callback=None, n_generation=1000, mutation='mutate_position_wise_ind', verbose=False):
        
        self.op = op
        self.better = better
        self.callback = callback
        self.n_generation = n_generation
        self.mutation = mutation
        self.verbose = verbose
                
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

        # online stats
        search_state = (individual, fitness_individual)
        if self.verbose: print(*search_state)
        if self.callback: self.callback(search_state)
    
        for _ in range(self.n_generation):
    
            offspring = self.op.mutate_ind(individual)            
            fitness_offspring = self.op.evaluate_ind(offspring)
    
            individual, fitness_individual = self.better([(individual, fitness_individual), (offspring, fitness_offspring)], key=lambda x : x[1])
        
            search_state = (individual, fitness_individual)
            if self.verbose: print(*search_state)
            if self.callback and self.callback(search_state): break            
        
        return search_state # return result object?

#---------------
