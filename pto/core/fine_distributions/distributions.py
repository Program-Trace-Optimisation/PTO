
from copy import copy, deepcopy
import random
from ..base import Dist, check_immutable
from .supp import rng_specs

class Random_real(Dist):
   """Handle continuous real-valued random variables within a range."""
   def __init__(self, fun, *args, val=None, **kwargs):
       super().__init__(fun, *args, val=val, **kwargs)
       self.min, self.max, self.range = rng_specs[fun].params(args, kwargs)
   
   def repair_val(self):
       self.val = min(max(self.min, self.val), self.max)
   
   @check_immutable
   def mutation(self):
       offspring = copy(self)
       offspring.val = self.val + random.gauss(0, 0.1*self.range)
       offspring.repair_val()
       return offspring

   @check_immutable
   def crossover(self, other):
       if self.fun.__name__ == other.fun.__name__:
           offspring = copy(self)
           offspring.val = random.uniform(self.val, other.val)
           return offspring
       return super().crossover(other)
   
   @check_immutable
   def convex_crossover(self, other1, other2):
       if self.fun.__name__ == other1.fun.__name__ and self.fun.__name__ == other2.fun.__name__: 
           offspring = copy(self)
           min_val = min(self.val, other1.val, other2.val)
           max_val = max(self.val, other1.val, other2.val)
           offspring.val = random.uniform(min_val, max_val)
           return offspring
       return super().convex_crossover(other1, other2)

   @check_immutable
   def distance(self, other):
       if self.fun.__name__ == other.fun.__name__:
           return min(1, abs(self.val - other.val)/self.range)
       return super().distance(other)
   
   def size(self):
       return 10
   
   def repair(self, other):
       if self.fun.__name__ == other.fun.__name__:
           self.val = ((other.val-other.min)/other.range)*self.range+self.min
           self.repair_val()
       else:
           super().repair(other)

class Random_int(Dist):
   """Handle discrete integer variables with step size."""
   def __init__(self, fun, *args, val=None, **kwargs):
       super().__init__(fun, *args, val=val, **kwargs)
       self.min, self.max, self.step = rng_specs[fun].params(args, kwargs)
   
   def repair_val(self):
       round_val = self.min + round((self.val - self.min) / self.step) * self.step
       self.val = min(max(self.min, round_val), self.max)
   
   @check_immutable
   def mutation(self):
       offspring = copy(self)
       for _ in range(10):
           offspring.val = self.val + random.choice([-1, 1]) * self.step
           offspring.repair_val()
           if offspring.val != self.val: break
       return offspring

   @check_immutable
   def crossover(self, other):
       if self.fun.__name__ == other.fun.__name__:
           offspring = copy(self)
           min_val = min(self.val, other.val)
           max_val = max(self.val, other.val)
           offspring.val = random.randint(min_val, max_val)
           return offspring
       return super().crossover(other)
   
   @check_immutable
   def convex_crossover(self, other1, other2):
       if self.fun.__name__ == other1.fun.__name__ and self.fun.__name__ == other2.fun.__name__: 
           offspring = copy(self)
           min_val = min(self.val, other1.val, other2.val)
           max_val = max(self.val, other1.val, other2.val)
           offspring.val = random.randint(min_val, max_val)
           return offspring
       return super().convex_crossover(other1, other2)

   @check_immutable
   def distance(self, other):
       if self.fun.__name__ == other.fun.__name__:
           return min(1, abs(self.val - other.val)/(self.max-self.min))
       return super().distance(other)
   
   def size(self):
       return (self.max-self.min)/self.step

   def repair(self, other):
       if self.fun.__name__ == other.fun.__name__:
           self.val = ((other.val-other.min)/other.step)*self.step+self.min
           self.repair_val()
       else:
           super().repair(other)

class Random_cat(Dist):
   """Handle categorical variables from a fixed sequence."""
   def __init__(self, fun, *args, val=None, **kwargs):
       super().__init__(fun, *args, val=val, **kwargs)
       self.seq = rng_specs[fun].params(args, kwargs)
   
   def repair_val(self):
       if self.val not in self.seq:
           self.val = random.choice(self.seq)

   @check_immutable
   def mutation(self):
       offspring = copy(self)
       if len(set(self.seq)) >= 2:
           offspring.val = random.choice([v for v in self.seq if v != self.val])
       return offspring
   
   def size(self):
       return len(self.seq)

   def repair(self, other):
       if self.fun.__name__ == other.fun.__name__:
           if other.val in self.seq:
               self.val = other.val
           else:
               diff_seq = [val for val in self.seq if val not in other.seq]
               self.val = random.choice(diff_seq) if diff_seq else random.choice(self.seq)
       else:
           super().repair(other)

# TODO: for the class seq, implement separate search operators 
# for non-replacement (shuffle, sample) and with-replacement (choices) functions

class Random_seq(Dist):
   """Handle sequences of k unique items from a larger sequence."""
   def __init__(self, fun, *args, val=None, **kwargs):
       super().__init__(fun, *args, val=val, **kwargs)
       self.sequence, self.k = rng_specs[fun].params(args, kwargs)
       
   def repair_val(self):
       if not self.val or len(self.val) != self.k:
           self.val = random.sample(self.sequence, self.k)
   
   def _rnd_swap(self, seq):
       if len(seq) >= 2:
           i,j = random.sample(range(len(seq)), 2)
           seq[i], seq[j] = seq[j], seq[i]

   def _rnd_replace(self, seq_to, seq_from, exclusive=False):
       idx = random.randrange(len(seq_to)) 
       valid_choices = [x for x in seq_from if x not in seq_to] if exclusive else seq_from
       if valid_choices:
            seq_to[idx] = random.choice(valid_choices)

   @check_immutable
   def mutation(self):
       
       offspring = deepcopy(self)

       # feasible mutation for shuffle is swap
       if self.fun.__name__ == 'shuffle':
           self._rnd_swap(offspring.val)

       # feasible mutation for sample is swap + excluisive replace
       elif self.fun.__name__ == 'sample':
           if random.random() < 0.5:
               self._rnd_swap(offspring.val)
           else:
               self._rnd_replace(offspring.val, self.sequence, exclusive=True)

       # feasible mutation for choices is non-exclusive replace
       else: # self.fun.__name__ == 'choices'
           self._rnd_replace(offspring.val, self.sequence)

       return offspring
   
   @check_immutable
   def crossover(self, other):
       if self.fun.__name__ == other.fun.__name__:
           offspring = copy(self)
           if len(set(self.sequence)) >= 2:
               combined = list(set(self.val) | set(other.val))
               if len(combined) >= self.k:
                   offspring.val = tuple(random.sample(combined, self.k))
               else:
                   needed = self.k - len(combined)
                   remaining = [x for x in self.sequence if x not in combined]
                   additional = random.sample(remaining, needed)
                   offspring.val = tuple(combined + additional)
           return offspring
       return super().crossover(other)

   @check_immutable
   def convex_crossover(self, other1, other2):
       if self.fun.__name__ == other1.fun.__name__ and self.fun.__name__ == other2.fun.__name__:
           offspring = copy(self)
           if len(set(self.sequence)) >= 2:
               combined = list(set(self.val) | set(other1.val) | set(other2.val))
               if len(combined) >= self.k:
                   offspring.val = tuple(random.sample(combined, self.k))
               else:
                   needed = self.k - len(combined)
                   remaining = [x for x in self.sequence if x not in combined]
                   additional = random.sample(remaining, needed)
                   offspring.val = tuple(combined + additional)
           return offspring
       return super().convex_crossover(other1, other2)
   
   def size(self):
       return min(len(self.sequence), self.k)
   
   def repair(self, other):
       if self.fun.__name__ == other.fun.__name__:
           if len(other.val) == self.k:
               preserved = [x for x in other.val if x in self.sequence]
               needed = self.k - len(preserved)
               if needed > 0:
                   available = [x for x in self.sequence if x not in preserved]
                   additional = random.sample(available, min(needed, len(available)))
                   self.val = tuple(preserved + additional)
               else:
                   self.val = tuple(preserved[:self.k])
           else:
               self.val = random.sample(self.sequence, self.k)
       else:
           super().repair(other)