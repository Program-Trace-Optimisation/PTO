
from copy import copy
import random

from ..base import Dist, check_immutable

from .supp import supp

#############################
# Real-valued distributions #
#############################

class Random_real(Dist): # class for real-valued distributions

  def __init__(self, fun, *args, val=None):
    super().__init__(fun, *args, val=val)
    self.min, self.max, self.range = supp[fun][1](args)
    
  # alter self
  def repair_val(self): # real --> supp
    self.val = min(max(self.min, self.val), self.max) # fix val
    
  @check_immutable  
  def mutation(self):
    offspring = copy(self)
    offspring.val = self.val + random.gauss(0, 0.1*self.range)  # mut val
    offspring.repair_val()
    return offspring

  @check_immutable
  def crossover(self, other):
    if type(self) == type(other):
        offspring = copy(self) 
        offspring.val = random.uniform(self.val, other.val) # blend recombination
    else:
        offspring = random.choice([self, other]) # discrete recombination
    return offspring

#########################
# Integer distributions #
#########################

class Random_int(Dist): # class for integer-valued distributions

  def __init__(self, fun, *args, val=None):
    super().__init__(fun, *args, val=val)
    self.min, self.max, self.step = supp[fun][1](args)  
    
  # alter self
  def repair_val(self): # real--> supp
    round_val = self.min + round((self.val - self.min) / self.step) * self.step
    self.val = min(max(self.min, round_val), self.max) # fix val
  
  @check_immutable
  def mutation(self):
    offspring = copy(self)
    for _ in range(10): # multiple attempt at producing a mutated offspring 
        offspring.val = self.val + random.choice([-1, 1]) * self.step  # mut val
        offspring.repair_val()
        if offspring.val != self.val: break
    return offspring

  @check_immutable
  def crossover(self, other):
    if type(self) == type(other):
        offspring = copy(self)
        min_val, max_val = (self.val, other.val) if self.val <= other.val else (other.val, self.val)
        offspring.val = random.randint(min_val, max_val) # blend recombination
    else:
        offspring = random.choice([self, other]) # discrete recombination
    return offspring

#############################
# Categorical distributions #
#############################

class Random_cat(Dist):
    
  def __init__(self, fun, *args, val=None):
    super().__init__(fun, *args, val=val)
    self.seq = supp[fun][1](args)
    self.args = (copy(self.args[0]),)  
    
  def repair_val(self): # sym --> supp
    if self.val not in self.seq:
      self.val = random.choice(self.seq) # fix val

  @check_immutable
  def mutation(self): # supp --> supp
    offspring = copy(self)
    if len(set(self.seq)) >= 2: # at least two distinct elements
      offspring.val = random.choice(self.seq)
      while(offspring.val == self.val):
        offspring.val = random.choice(self.seq)
      #print(offspring.val)
    return offspring

  # crossover inherited from base class
