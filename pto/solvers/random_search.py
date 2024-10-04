
from pto.solvers import HC

# RANDOM SEARCH

''' Random search can be implemented as a hill-climber whose mutation is completely random 
    and does not depend on the current solution. '''

def RS(op, **kwargs):
    kwargs['mutation'] = 'mutate_random_ind'
    return HC(op, **kwargs)
