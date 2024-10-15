
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
        return offspring
    return super().crossover(other)
  
  @check_immutable
  def convex_crossover(self, other1, other2):
    if type(self) == type(other1) == type(other2):
      offspring = copy(self)
      min_val = min(self.val, other1.val, other2.val)
      max_val = max(self.val, other1.val, other2.val)
      offspring.val = random.uniform(min_val, max_val) # blend recombination
      return offspring
    return super().convex_crossover(other1, other2)

  @check_immutable
  def distance(self, other):
    return float(type(self) != type(other) or min(1, abs(self.val - other.val)/self.range))
  
  def repair(self, other): # alter self
    if type(self) == type(other): # if trace entry compatible
        # trace value adpatation: align on min and rescale on range size
        self.val = ((other.val-other.min)/other.range)*self.range+self.min # recycle and adapt trace value 
        self.repair_val() # and repair it
    else: # if incompatible
        self.sample() # resample
    
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
        return offspring
    return super().crossover(other)
  
  @check_immutable
  def convex_crossover(self, other1, other2):
    if type(self) == type(other1) == type(other2):
      offspring = copy(self)
      min_val = min(self.val, other1.val, other2.val)
      max_val = max(self.val, other1.val, other2.val)
      offspring.val = random.randint(min_val, max_val) # blend recombination
      return offspring
    return super().convex_crossover(other1, other2)

  @check_immutable
  def distance(self, other):
    return float(type(self) != type(other) or min(1, abs(self.val - other.val)/(self.max-self.min)))

  def repair(self, other): # alter self
      if type(self) == type(other): # if trace entry compatible
          # trace value adpatation: align on min and rescale on step size
          self.val = ((other.val-other.min)/other.step)*self.step+self.min # recycle and adapt trace value 
          self.repair_val() # and repair it
      else: # if incompatible
          self.sample() # resample 

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

  # convex crossover inherited from base class

  # distance inherited from base class

  def repair(self, other): # alter self
      if type(self) == type(other): # if trace entry compatible
          # trace value adpatation: reuse value if available, 
          # or try an available value not available in trace
          if other.val in self.seq:
              self.val = other.val  
          else:
              diff_seq = [val for val in self.seq if val not in other.seq]
              self.val = random.choice(diff_seq) if diff_seq else random.choice(self.seq)  # recycle and adapt trace value 
          #self.repair_val() # and repair it
      else: # if incompatible
          self.sample() # resample  

