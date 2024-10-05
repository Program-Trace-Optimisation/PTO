
from pto.solvers import hill_climber

# RANDOM SEARCH

''' Random search can be implemented as a hill-climber whose mutation is completely random 
    and does not depend on the current solution. '''

def random_search(op, **kwargs):
    kwargs['mutation'] = 'mutate_random_ind'
    return hill_climber(op, **kwargs)
