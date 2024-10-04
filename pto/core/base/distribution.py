
from copy import copy
import random

from .check_immutable import check_immutable

class Dist(): # base class
  
    def __init__(self, fun, *args, val = None):
        self.fun = fun
        self.args = tuple(copy(arg) for arg in args) # args
        self.val = val
    
    def sample(self): # alter self
        self.val = self.fun(*self.args)

    def repair(self, _): # alter self
        self.sample()
    
    @check_immutable 
    def mutation(self): # does not alter self
        offspring = copy(self)
        offspring.sample()
        return offspring
    
    @check_immutable 
    def crossover(self, other): # does not alter self and other
        offspring = random.choice([self, other])
        #offspring = copy(offspring)
        return offspring
    
    def __repr__(self):
        return f'{self.__class__.__name__}({self.fun.__name__}, {self.args},  val={self.val})' 
        #return self.__class__.__name__ + str((self.fun.__name__, self.args, self.val))

    def __eq__(self, other):
        return (self.fun.__name__ == other.fun.__name__) and (self.args == other.args) and (self.val == other.val)
