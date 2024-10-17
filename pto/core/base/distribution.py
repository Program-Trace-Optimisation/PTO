
from copy import copy
import random

from .check_immutable import check_immutable

class Dist():
  
    def __init__(self, fun, *args, val = None):
        self.fun = fun
        self.args = tuple(copy(arg) for arg in args)
        self.val = val
    
    def sample(self):
        self.val = self.fun(*self.args)

    def repair(self, _):
        self.sample()
    
    @check_immutable 
    def mutation(self):
        offspring = copy(self)
        offspring.sample()
        return offspring
    
    @check_immutable 
    def crossover(self, other):
        return random.choice([self, other])
    
    @check_immutable 
    def convex_crossover(self, other1, other2):
        return random.choice([self, other1, other2])
    
    @check_immutable
    def distance(self, other):
        return float(self != other)
    
    def __repr__(self):
        return f'{self.__class__.__name__}({self.fun.__name__}, {self.args}, val={self.val})' 
    
    def __eq__(self, other):
        return (self.fun.__name__ == other.fun.__name__ and 
                self.args == other.args and 
                self.val == other.val)
